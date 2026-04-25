#!/usr/bin/env bash
set -euo pipefail

VENDOR_DIR="vendor/netease_url"
VENDOR_REPO="https://github.com/Suxiaoqinx/Netease_url.git"
VENDOR_REF="${VENDOR_REF:-main}"

mkdir -p vendor

if [ -d "$VENDOR_DIR/.git" ]; then
  git -C "$VENDOR_DIR" fetch --depth 1 origin "$VENDOR_REF"
  git -C "$VENDOR_DIR" checkout FETCH_HEAD
else
  git clone --depth 1 --branch "$VENDOR_REF" "$VENDOR_REPO" "$VENDOR_DIR" 2>/dev/null || \
    git clone --depth 1 "$VENDOR_REPO" "$VENDOR_DIR"
fi

git -C "$VENDOR_DIR" rev-parse HEAD > .vendor-sha
echo "Pinned Netease_url to $(cat .vendor-sha)"
