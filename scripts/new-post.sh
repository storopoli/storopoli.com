#!/usr/bin/env bash
# Scaffold a new post: scripts/new-post.sh my-post-slug
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "usage: $0 <slug>" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
slug="$1"
date="$(date +%F)"
file="$ROOT/posts/$date-$slug.md"

if [ -e "$file" ]; then
  echo "error: $file already exists" >&2
  exit 1
fi

cat > "$file" <<EOF
---
title: TODO
date: $date
author: Jose Storopoli
description: TODO
tags: []
---

TODO
EOF

echo "created $file"
