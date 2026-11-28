#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pillow==13.0.0",
# ]
# ///
"""Optimize static images into _site/ at build time (never mutating static/).

- Raster images (.jpg, .jpeg, .png, .webp) under static/images/ and static/pp.jpg:
  * Apply EXIF orientation (exif_transpose) and strip EXIF/GPS/XMP/comment metadata.
  * Convert non-sRGB ICC profiles (e.g. Display P3) to sRGB before dropping profiles.
  * Downscale wider-than-target images (1600px max width for content images, 400px
    for pp.jpg), preserving aspect ratio and never upscaling.
  * Re-encode fallbacks (progressive optimized JPEG, optimized PNG, or WebP), keeping
    original bytes when unmodified/metadata-free and re-encoding wouldn't shrink them.
  * Emit a sibling .webp variant for non-WebP images only when smaller than the
    optimized fallback (and without colliding with an existing .webp source).
- SVG images under static/images/:
  * Left untouched; intrinsic width/height are parsed for the manifest to prevent CLS.
- Outputs are cached in <cache_dir> keyed by SHA-256 of source bytes + settings.
- Writes <manifest_path> mapping local URLs (/images/..., /pp.jpg) to
  {"width": int, "height": int[, "webp": "/..."]}.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import threading
import xml.etree.ElementTree as ET

from PIL import Image, ImageCms, ImageOps

CACHE_SCHEMA_VERSION = 1
MAX_WIDTH = 1600
MAX_WIDTH_OVERRIDES = {
    "pp.jpg": 400,
}
JPEG_QUALITY = 82
WEBP_QUALITY = 82
WEBP_METHOD = 6
WEBP_LOSSLESS_METHOD = 4

RASTER_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
SETTINGS_SIG = (
    f"v={CACHE_SCHEMA_VERSION}|jq={JPEG_QUALITY}|wq={WEBP_QUALITY}"
    f"|wm={WEBP_METHOD}|wlm={WEBP_LOSSLESS_METHOD}"
)
# Metadata keys that contain EXIF, XMP, camera/editor metadata, comments, or
# multi-picture auxiliary frames (e.g. Apple MPO gain/depth maps) and must be stripped.
STRIP_META_KEYS = frozenset(
    {"exif", "xmp", "XML:com.adobe.xmp", "photoshop", "comment", "mp"}
)
SVG_LEN_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*(?:px)?\s*$")


def atomic_write_bytes(path: Path, data: bytes) -> None:
    tmp = path.parent / f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def parse_svg_dimensions(svg_path: Path) -> tuple[int, int] | None:
    """Return integer (width, height) for an SVG, or None if indeterminate."""
    try:
        root = ET.parse(svg_path).getroot()
    except (ET.ParseError, OSError):
        return None

    def parse_len(val: str | None) -> float | None:
        if not val:
            return None
        m = SVG_LEN_RE.match(val)
        return float(m.group(1)) if m else None

    w = parse_len(root.attrib.get("width"))
    h = parse_len(root.attrib.get("height"))
    if w and h and w > 0 and h > 0:
        return (max(1, round(w)), max(1, round(h)))

    vb = root.attrib.get("viewBox")
    if vb:
        parts = [p for p in re.split(r"[\s,]+", vb.strip()) if p]
        if len(parts) == 4:
            try:
                vb_w = float(parts[2])
                vb_h = float(parts[3])
                if vb_w > 0 and vb_h > 0:
                    return (max(1, round(vb_w)), max(1, round(vb_h)))
            except ValueError:
                return None
    return None


def convert_icc_to_srgb(im: Image.Image, icc: bytes | None) -> tuple[Image.Image, bool]:
    """Convert non-sRGB ICC-tagged RGB/RGBA images to sRGB so profiles can be dropped."""
    if not icc or im.mode not in ("RGB", "RGBA"):
        return im, False
    try:
        src_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        desc = ImageCms.getProfileDescription(src_profile).strip().lower()
        if "srgb" in desc:
            return im, False
        srgb_profile = ImageCms.createProfile("sRGB")
        converted = ImageCms.profileToProfile(
            im, src_profile, srgb_profile, outputMode=im.mode
        )
        return (converted if converted is not None else im), True
    except Exception:
        return im, False


def prepare_for_jpeg(im: Image.Image) -> Image.Image:
    if im.mode in ("RGB", "L"):
        return im
    if im.mode in ("RGBA", "LA", "PA") or (
        im.mode == "P" and "transparency" in im.info
    ):
        rgba = im.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.getchannel("A"))
        return bg
    return im.convert("RGB")


def prepare_for_webp(im: Image.Image) -> Image.Image:
    if im.mode in ("RGB", "RGBA", "L"):
        return im
    if im.mode == "P":
        return im.convert("RGBA" if "transparency" in im.info else "RGB")
    if im.mode in ("LA", "PA"):
        return im.convert("RGBA")
    return im.convert("RGB")


def encode_raster(
    raw_bytes: bytes,
    ext: str,
    max_width: int,
    can_emit_webp: bool,
) -> tuple[int, int, bytes, bytes | None]:
    """Optimize one raster image; returns (width, height, fallback_bytes, webp_bytes|None)."""
    with Image.open(io.BytesIO(raw_bytes)) as src_im:
        # Preserve animated WebP without collapsing frames.
        if (
            ext == ".webp"
            and getattr(src_im, "is_animated", False)
            and getattr(src_im, "n_frames", 1) > 1
        ):
            return src_im.width, src_im.height, raw_bytes, None

        exif = src_im.getexif()
        orig_orient = exif.get(274) if exif else None
        reoriented = orig_orient not in (None, 1)
        has_meta = (
            bool(exif)
            or src_im.format == "MPO"
            or any(k in src_im.info for k in STRIP_META_KEYS)
        )
        icc = src_im.info.get("icc_profile")

        im = ImageOps.exif_transpose(src_im)
        im, icc_converted = convert_icc_to_srgb(im, icc)

        resized = False
        if im.width > max_width:
            if im.mode == "P":
                im = im.convert("RGBA" if "transparency" in im.info else "RGB")
            new_h = max(1, round(im.height * (max_width / im.width)))
            im = im.resize((max_width, new_h), Image.Resampling.LANCZOS)
            resized = True

        # Drop redundant fully opaque alpha channels (common in screenshots/PNGs).
        if im.mode == "RGBA" and im.getchannel("A").getextrema() == (255, 255):
            im = im.convert("RGB")

        # Pillow encoders (notably JPEG `comment`) implicitly inherit some keys
        # from `im.info`; strip them explicitly before saving.
        for key in (*STRIP_META_KEYS, "icc_profile"):
            im.info.pop(key, None)

        width, height = im.size

        fb_buf = io.BytesIO()
        if ext in (".jpg", ".jpeg"):
            prepare_for_jpeg(im).save(
                fb_buf,
                format="JPEG",
                quality=JPEG_QUALITY,
                optimize=True,
                progressive=True,
            )
        elif ext == ".png":
            im.save(fb_buf, format="PNG", optimize=True, compress_level=9)
        elif ext == ".webp":
            prepare_for_webp(im).save(
                fb_buf,
                format="WEBP",
                quality=WEBP_QUALITY,
                method=WEBP_METHOD,
            )
        else:
            raise ValueError(f"Unsupported extension: {ext}")
        fb_bytes = fb_buf.getvalue()

        # Avoid bloating or re-compressing already-optimal, metadata-free, unresized images.
        if (
            not resized
            and not reoriented
            and not has_meta
            and not icc_converted
            and len(fb_bytes) >= len(raw_bytes)
        ):
            fb_bytes = raw_bytes

        webp_bytes: bytes | None = None
        if can_emit_webp:
            webp_im = prepare_for_webp(im)
            lossy_buf = io.BytesIO()
            webp_im.save(
                lossy_buf,
                format="WEBP",
                quality=WEBP_QUALITY,
                method=WEBP_METHOD,
            )
            candidate = lossy_buf.getvalue()
            if ext == ".png":
                lossless_buf = io.BytesIO()
                webp_im.save(
                    lossless_buf,
                    format="WEBP",
                    lossless=True,
                    method=WEBP_LOSSLESS_METHOD,
                )
                ll_bytes = lossless_buf.getvalue()
                if len(ll_bytes) < len(candidate):
                    candidate = ll_bytes
            if len(candidate) < len(fb_bytes):
                webp_bytes = candidate

        return width, height, fb_bytes, webp_bytes


def process_raster(
    rel: Path,
    static_dir: Path,
    site_dir: Path,
    cache_dir: Path,
    source_rels: set[str],
) -> dict[str, object]:
    rel_posix = rel.as_posix()
    ext = rel.suffix.lower()
    src_path = static_dir / rel
    dst_path = site_dir / rel
    webp_rel = rel.with_suffix(".webp")
    webp_rel_posix = webp_rel.as_posix()
    webp_dst_path = site_dir / webp_rel

    raw_bytes = src_path.read_bytes()
    orig_size = len(raw_bytes)
    max_width = MAX_WIDTH_OVERRIDES.get(rel_posix, MAX_WIDTH)
    can_emit_webp = (ext != ".webp") and (webp_rel_posix not in source_rels)

    digest = hashlib.sha256()
    digest.update(
        f"{SETTINGS_SIG}|max_w={max_width}|ext={ext}|webp={int(can_emit_webp)}|".encode()
    )
    digest.update(raw_bytes)
    key = digest.hexdigest()[:32]

    meta_path = cache_dir / f"{key}.meta.json"
    fb_cache = cache_dir / f"{key}{ext}"
    webp_cache = cache_dir / f"{key}.webp"

    cached = False
    width: int | None = None
    height: int | None = None
    has_webp = False
    fb_size = 0
    webp_size: int | None = None

    if meta_path.is_file() and fb_cache.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if (
                meta.get("v") == CACHE_SCHEMA_VERSION
                and isinstance(meta.get("width"), int)
                and isinstance(meta.get("height"), int)
                and (not meta.get("has_webp") or webp_cache.is_file())
            ):
                width = meta["width"]
                height = meta["height"]
                has_webp = bool(meta.get("has_webp"))
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fb_cache, dst_path)
                fb_size = fb_cache.stat().st_size
                if has_webp:
                    shutil.copy2(webp_cache, webp_dst_path)
                    webp_size = webp_cache.stat().st_size
                elif can_emit_webp:
                    webp_dst_path.unlink(missing_ok=True)
                cached = True
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            cached = False

    if not cached:
        width, height, fb_bytes, webp_bytes = encode_raster(
            raw_bytes, ext, max_width, can_emit_webp
        )
        has_webp = webp_bytes is not None
        fb_size = len(fb_bytes)
        webp_size = len(webp_bytes) if webp_bytes is not None else None

        atomic_write_bytes(fb_cache, fb_bytes)
        if webp_bytes is not None:
            atomic_write_bytes(webp_cache, webp_bytes)
        meta = {
            "v": CACHE_SCHEMA_VERSION,
            "width": width,
            "height": height,
            "has_webp": has_webp,
        }
        # Write metadata last so it acts as the cache-entry commit marker.
        atomic_write_text(meta_path, json.dumps(meta, sort_keys=True))

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_bytes(dst_path, fb_bytes)
        if webp_bytes is not None:
            atomic_write_bytes(webp_dst_path, webp_bytes)
        elif can_emit_webp:
            webp_dst_path.unlink(missing_ok=True)

    entry: dict[str, object] = {"width": width, "height": height}
    if has_webp:
        entry["webp"] = "/" + webp_rel_posix

    return {
        "href": "/" + rel_posix,
        "entry": entry,
        "orig_size": orig_size,
        "fb_size": fb_size,
        "webp_size": webp_size,
        "cached": cached,
    }


def collect_image_paths(static_dir: Path) -> list[Path]:
    paths: list[Path] = []
    images_dir = static_dir / "images"
    if images_dir.is_dir():
        for p in sorted(images_dir.rglob("*")):
            if p.is_file():
                paths.append(p.relative_to(static_dir))
    pp = static_dir / "pp.jpg"
    if pp.is_file():
        paths.append(Path("pp.jpg"))
    return sorted(paths, key=lambda p: p.as_posix())


def fmt_mib(num_bytes: int) -> str:
    return f"{num_bytes / (1024 * 1024):.2f} MiB"


def main(argv: list[str] | None = None) -> int:
    default_jobs = int(os.environ.get("JOBS", os.cpu_count() or 4))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jobs",
        type=int,
        default=max(1, default_jobs),
        help="Max parallel worker threads (default: $JOBS or CPU count)",
    )
    parser.add_argument("static_dir", type=Path)
    parser.add_argument("site_dir", type=Path)
    parser.add_argument("cache_dir", type=Path)
    parser.add_argument("manifest_path", type=Path)
    args = parser.parse_args(argv)

    static_dir: Path = args.static_dir
    site_dir: Path = args.site_dir
    cache_dir: Path = args.cache_dir
    manifest_path: Path = args.manifest_path
    jobs = max(1, args.jobs)

    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    all_rels = collect_image_paths(static_dir)
    source_rels = {p.as_posix() for p in all_rels}

    raster_rels = [p for p in all_rels if p.suffix.lower() in RASTER_EXTS]
    svg_rels = [p for p in all_rels if p.suffix.lower() == ".svg"]

    manifest: dict[str, dict[str, object]] = {}

    for rel in svg_rels:
        dims = parse_svg_dimensions(static_dir / rel)
        if dims is not None:
            manifest["/" + rel.as_posix()] = {"width": dims[0], "height": dims[1]}

    results: list[dict[str, object]] = []
    if jobs == 1 or len(raster_rels) <= 1:
        for rel in raster_rels:
            results.append(
                process_raster(rel, static_dir, site_dir, cache_dir, source_rels)
            )
    else:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = [
                pool.submit(
                    process_raster, rel, static_dir, site_dir, cache_dir, source_rels
                )
                for rel in raster_rels
            ]
            for fut in futures:
                results.append(fut.result())

    total_orig = 0
    total_fb = 0
    total_best = 0
    webp_count = 0
    cached_count = 0

    for res in results:
        href = str(res["href"])
        manifest[href] = res["entry"]  # type: ignore[assignment]
        orig_sz = int(res["orig_size"])  # type: ignore[arg-type]
        fb_sz = int(res["fb_size"])  # type: ignore[arg-type]
        webp_sz = res["webp_size"]
        total_orig += orig_sz
        total_fb += fb_sz
        if isinstance(webp_sz, int):
            total_best += webp_sz
            webp_count += 1
        else:
            total_best += fb_sz
        if res["cached"]:
            cached_count += 1

    atomic_write_text(
        manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )

    print(
        f"    {len(raster_rels)} raster images "
        f"({webp_count} WebP variants, {cached_count} cached): "
        f"{fmt_mib(total_orig)} -> {fmt_mib(total_fb)} fallback / {fmt_mib(total_best)} WebP"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
