#!/usr/bin/env bash
# Build storopoli.com: markdown posts -> HTML via typst (+ cmarker), no SSG.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/_site"
CACHE="$ROOT/.cache"
# Parallelism for the independent per-file phases (override with JOBS=1 to
# serialize, e.g. when debugging a single failing input).
JOBS="${JOBS:-$(nproc 2>/dev/null || echo 4)}"

# Compile one typst input to HTML, failing on any diagnostic other than the
# known "html export is under active development" banner. This catches
# "equation was ignored", missing images, bad math, etc.
compile() {
  local src="$1" dst="$2"
  shift 2
  local diag
  if ! diag="$(typst compile --root "$ROOT" --features html --format html "$@" "$src" "$dst" 2>&1)"; then
    printf 'FAIL %s\n%s\n' "$src" "$diag" >&2
    return 1
  fi
  diag="$(printf '%s\n' "$diag" \
    | grep -v -e '^warning: html export is under active development' -e '^ = hint:' \
    | grep -v '^[[:space:]]*$' || true)"
  if [ -n "$diag" ]; then
    printf 'FAIL (warnings) %s\n%s\n' "$src" "$diag" >&2
    return 1
  fi
}

# Compile + inject constant <head> links + relocate typst's endnotes.
build_page() {
  local src="$1" dst="$2"
  shift 2
  local tmp
  tmp="$(mktemp)"
  compile "$src" "$tmp" "$@"
  python3 "$ROOT/scripts/postprocess.py" "$CSS_HREF" < "$tmp" > "$dst"
  rm -f "$tmp"
}

slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr ' ' '-'
}

# --- per-item workers (one shell process per call, fanned out via xargs) ---

# Convert a single markdown file's body to typst markup.
convert_body() {
  local f="$1" name
  name="$(basename "$f" .md)"
  pandoc "$f" --from markdown --to typst \
    --shift-heading-level-by=-1 --wrap=none \
    --lua-filter "$ROOT/scripts/body-filter.lua" \
    > "$CACHE/bodies/$name.typ"
}

# Query a single post's frontmatter metadata into its own json shard.
collect_meta() {
  local f="$1" slug
  slug="$(basename "$f" .md)"
  typst eval --root "$ROOT" --features html \
    --input "path=/posts/$slug.md" \
    --input "body=/.cache/bodies/$slug.typ" \
    --in lib/post.typ 'query(<frontmatter>).first().value' \
    | jq --arg slug "$slug" '. + {slug: $slug, url: ("/posts/" + $slug + ".html")}' \
    > "$CACHE/meta/$slug.json"
}

# Build a single post HTML page.
build_post() {
  local f="$1" slug
  slug="$(basename "$f" .md)"
  build_page "$ROOT/lib/post.typ" "$OUT/posts/$slug.html" \
    --input "path=/posts/$slug.md" --input "body=/.cache/bodies/$slug.typ"
}

# Build a single standalone page HTML.
build_standalone() {
  local f="$1" name
  name="$(basename "$f" .md)"
  build_page "$ROOT/lib/page.typ" "$OUT/$name.html" \
    --input "path=/pages/$name.md" --input "body=/.cache/bodies/$name.typ"
}

# Build a single listing page from a "kind[:tag]" spec.
build_listing() {
  local kind="${1%%:*}" tag="${1#*:}"
  if [ "$kind" = tag ]; then
    build_page "$ROOT/lib/listing.typ" "$OUT/tags/$(slugify "$tag").html" \
      --input kind=tag --input "tag=$tag"
  else
    build_page "$ROOT/lib/listing.typ" "$OUT/$kind.html" --input "kind=$kind"
  fi
}

# Run a worker function over a NUL-delimited list of items, JOBS at a time.
# Each item becomes the single argument of one `worker` call; any failure
# (xargs exits non-zero) aborts the build via the surrounding pipefail/set -e.
fanout() {
  local worker="$1"
  xargs -0 -P "$JOBS" -I{} bash -c 'set -euo pipefail; '"$worker"' "$@"' _ {}
}

export -f compile build_page slugify convert_body collect_meta \
  build_post build_standalone build_listing
export ROOT OUT CACHE

echo "==> Cleaning"
rm -rf "$OUT" "$CACHE"
mkdir -p "$OUT/posts" "$OUT/tags" "$CACHE/bodies" "$CACHE/meta"

echo "==> Copying static files"
cp -R "$ROOT/static/." "$OUT/"

# Fingerprint the stylesheet: pages link /css/site.<hash>.css so a deploy
# can never pair new HTML with a stale cached stylesheet (the Cloudflare
# edge in front of GitHub Pages caches assets with a 4h browser TTL).
# The unhashed copy stays in place as a stable URL.
CSS_HASH="$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest()[:8])' "$ROOT/static/css/site.css")"
CSS_HREF="/css/site.$CSS_HASH.css"
cp "$OUT/css/site.css" "$OUT$CSS_HREF"
export CSS_HREF

shopt -s nullglob
posts=("$ROOT"/posts/*.md)
pages=("$ROOT"/pages/*.md)

echo "==> Converting markdown bodies with pandoc"
printf '%s\0' "${posts[@]}" "${pages[@]}" | fanout convert_body

echo "==> Collecting post metadata"
printf '%s\0' "${posts[@]}" | fanout collect_meta
jq -s 'sort_by(.date) | reverse' "$CACHE"/meta/*.json > "$CACHE/posts.json"

echo "==> Building posts ($(jq length "$CACHE/posts.json"))"
printf '%s\0' "${posts[@]}" | fanout build_post

echo "==> Building pages"
printf '%s\0' "${pages[@]}" | fanout build_standalone

echo "==> Building listings"
{
  printf 'index\0archive\0'
  jq -r '[.[].tags[]] | unique | .[] | "tag:" + .' "$CACHE/posts.json" | tr '\n' '\0'
} | fanout build_listing

echo "==> Checking for silently escaped raw HTML"
# cmarker only parses raw HTML tags written on a single line; multi-line
# tags get HTML-escaped into visible text without any build error.
# Escaped tags inside <code>/<pre> are legitimate (posts talk about HTML).
python3 - "$OUT" <<'PYCHECK'
import re, sys
from pathlib import Path

bad = []
for f in Path(sys.argv[1]).rglob("*.html"):
    html = f.read_text()
    prose = re.sub(r"<(code|pre)\b.*?</\1>", "", html, flags=re.S)
    if re.search(r"&lt;(iframe|div|img|span)\b", prose):
        bad.append(str(f))
if bad:
    print("FAIL: escaped raw HTML outside code blocks (multi-line tag in a post?)",
          *bad, sep="\n", file=sys.stderr)
    sys.exit(1)
PYCHECK

echo "==> Generating atom.xml"
# Full-content feed: gen-feed.py lifts each post's body out of its built page
# (math, highlighting and footnotes included) into <content type="html">, so
# readers show the whole post instead of just the summary.
python3 "$ROOT/scripts/gen-feed.py" "$CACHE/posts.json" "$OUT" > "$OUT/atom.xml"

echo "==> Done: $OUT"
