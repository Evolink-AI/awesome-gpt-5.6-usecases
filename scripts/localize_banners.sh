#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec xcrun swift "$repo_root/scripts/localize_banners.swift" "$repo_root"
