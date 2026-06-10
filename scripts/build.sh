#!/usr/bin/env bash
# Build storopoli.com: markdown posts -> HTML via typst (+ cmarker), no SSG.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/_site"
CACHE="$ROOT/.cache"
TYPST_FLAGS=(--root "$ROOT" --features html)

# Compile one typst input to HTML, failing on any diagnostic other than the
# known "html export is under active development" banner. This catches
# "equation was ignored", missing images, bad math, etc.
compile() {
  local src="$1" dst="$2"
  shift 2
  local diag
  if ! diag="$(typst compile "${TYPST_FLAGS[@]}" --format html "$@" "$src" "$dst" 2>&1)"; then
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
  python3 "$ROOT/scripts/postprocess.py" < "$tmp" > "$dst"
  rm -f "$tmp"
}

slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr ' ' '-'
}

echo "==> Cleaning"
rm -rf "$OUT" "$CACHE"
mkdir -p "$OUT/posts" "$OUT/tags" "$CACHE"

echo "==> Copying static files"
cp -R "$ROOT/static/." "$OUT/"

echo "==> Collecting post metadata"
shopt -s nullglob
posts=("$ROOT"/posts/*.md)
{
  for f in "${posts[@]}"; do
    slug="$(basename "$f" .md)"
    typst query "${TYPST_FLAGS[@]}" --input "path=/posts/$slug.md" \
      lib/post.typ '<frontmatter>' --field value --one \
      | jq --arg slug "$slug" '. + {slug: $slug, url: ("/posts/" + $slug + ".html")}'
  done
} | jq -s 'sort_by(.date) | reverse' > "$CACHE/posts.json"

echo "==> Building posts ($(jq length "$CACHE/posts.json"))"
for f in "${posts[@]}"; do
  slug="$(basename "$f" .md)"
  build_page "$ROOT/lib/post.typ" "$OUT/posts/$slug.html" --input "path=/posts/$slug.md"
done

echo "==> Building pages"
for f in "$ROOT"/pages/*.md; do
  name="$(basename "$f" .md)"
  build_page "$ROOT/lib/page.typ" "$OUT/$name.html" --input "path=/pages/$name.md"
done

echo "==> Building listings"
build_page "$ROOT/lib/listing.typ" "$OUT/index.html" --input kind=index
build_page "$ROOT/lib/listing.typ" "$OUT/archive.html" --input kind=archive
while IFS= read -r tag; do
  [ -n "$tag" ] || continue
  build_page "$ROOT/lib/listing.typ" "$OUT/tags/$(slugify "$tag").html" \
    --input kind=tag --input "tag=$tag"
done < <(jq -r '[.[].tags[]] | unique | .[]' "$CACHE/posts.json")

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
jq -r --arg root "https://storopoli.com" '
  def esc: @html;
  def rfc: . + "T00:00:00Z";
  ( "<?xml version=\"1.0\" encoding=\"utf-8\"?>",
    "<feed xmlns=\"http://www.w3.org/2005/Atom\">",
    "  <title>Jose Storopoli, PhD</title>",
    "  <link href=\"\($root)/atom.xml\" rel=\"self\"/>",
    "  <link href=\"\($root)\"/>",
    "  <id>\($root)/atom.xml</id>",
    "  <updated>\((.[0].date // "2000-01-01") | rfc)</updated>",
    "  <author><name>Jose Storopoli, PhD</name><email>jose@storopoli.com</email></author>"
  ),
  ( .[0:10][]
    | "  <entry>",
      "    <title>\(.title | esc)</title>",
      "    <link href=\"\($root + .url)\"/>",
      "    <id>\($root + .url)</id>",
      "    <published>\(.date | rfc)</published>",
      "    <updated>\(.date | rfc)</updated>",
      "    <summary>\((.description // .title) | esc)</summary>",
      "  </entry>"
  ),
  "</feed>"
' "$CACHE/posts.json" > "$OUT/atom.xml"

echo "==> Done: $OUT"
