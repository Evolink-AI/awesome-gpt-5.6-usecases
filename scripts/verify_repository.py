#!/usr/bin/env python3
"""Verify the public GPT-5.6 usecase repository contract."""

from __future__ import annotations

import json
import hashlib
import re
import struct
import sys
from math import ceil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANGS = {
    "README.md": "images/en.png",
    "README_es.md": "images/es.png",
    "README_pt.md": "images/pt.png",
    "README_ja.md": "images/ja.png",
    "README_ko.md": "images/ko.png",
    "README_de.md": "images/de.png",
    "README_fr.md": "images/fr.png",
    "README_tr.md": "images/tr.png",
    "README_zh-TW.md": "images/zh-tw.png",
    "README_zh-CN.md": "images/zh.png",
    "README_ru.md": "images/ru.png",
}
CATEGORY_ANCHORS = ["coding-and-builds", "agents-and-workflows", "creative-and-product-work", "evaluation-and-limits"]
CASE_RE = re.compile(
    r'^<a id="case-(?P<number>\d+)"></a>\n'
    r'^### Case (?P=number): \[(?P<title>[^\]]+)\]\((?P<source>[^)]+)\) '
    r'\(by \[(?P<author>[^\]]+)\]\((?P<author_url>[^)]+)\)\)\n\n'
    r'^\*\*(?P<takeaway>[^\n]+)\*\*\n\n'
    r'(?P<body>[^\n]+)\n\n'
    r'(?P<media>.*?)'
    r'^Type: (?P<type>Demo|Tutorial|Evaluation|Integration|Benchmark|Limit) \| Date: (?P<date>\d{4}-\d{2}-\d{2})$',
    re.MULTILINE | re.DOTALL,
)
BAD_MARKERS = ("TODO", "TBD", "translation pending", "translate to", "{{", "<placeholder>")
CANONICAL_BADGES = [
    "🇺🇸_English-Default_Source", "🇪🇸_Español-Ver", "🇵🇹_Português-Ver", "🇯🇵_日本語-表示",
    "🇰🇷_한국어-보기", "🇩🇪_Deutsch-Ansehen", "🇫🇷_Français-Voir", "🇹🇷_Türkçe-Görüntüle",
    "🇹🇼_繁體中文-查看", "🇨🇳_简体中文-查看", "🇷🇺_Русский-Смотреть",
]
QUICKSTART_URL = "https://docs.evolink.ai/en/api-manual/language-series/gpt-5.6/gpt-5.6-quickstart"
REFERENCE_URL = "https://docs.evolink.ai/en/api-manual/language-series/gpt-5.6/gpt-5.6-reference"


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def case_records(text: str) -> list[dict[str, str | int]]:
    return [
        {**match.groupdict(), "number": int(match.group("number")), "body": match.group("body").strip()}
        for match in CASE_RE.finditer(text)
    ]


def png_dimensions(path: Path) -> tuple[int, int] | None:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", header[16:24])


def verify() -> list[str]:
    errors: list[str] = []
    manifest_path = ROOT / "data" / "media-manifest.json"
    media_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    remote_media = media_manifest.get("files", {})
    data_path = ROOT / "data" / "gpt-5.6-usecase-curated.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    expected = data["items"]
    expected_count = len(expected)
    if expected_count < 1 or data.get("total_public_cases") != expected_count:
        fail(errors, "curated data total_public_cases must match the non-empty public case list")
    required_handoff = (
        "public_number", "dedup_key", "source_url", "author_url", "author_handle", "title", "takeaway",
        "body_notes", "type", "date", "category", "decision", "decision_reason", "prompt_boundary", "media_type",
    )
    for item in expected:
        for field in required_handoff:
            value = item.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                fail(errors, f"curated case {item.get('public_number')} missing handoff field {field}")
        if item.get("decision") != "high_confidence_update":
            fail(errors, f"curated case {item.get('public_number')} is not high_confidence_update")
        if len(str(item.get("title", "")).split()) > 10:
            fail(errors, f"curated case {item.get('public_number')} title exceeds 10 words")
        media_type = item.get("media_type")
        if media_type == "video":
            for field in ("poster_path", "poster_url", "playable_video_path", "playable_video_url"):
                if not item.get(field):
                    fail(errors, f"curated case {item.get('public_number')} missing video field {field}")
            for field in ("poster_path", "playable_video_path"):
                path = ROOT / str(item.get(field, ""))
                if path.exists() and (not path.is_file() or path.stat().st_size == 0):
                    fail(errors, f"curated case {item.get('public_number')} missing local video asset {field}")
        elif media_type == "image":
            paths = item.get("media_paths", [])
            urls = item.get("r2_media_urls", [])
            if not paths or len(paths) != len(urls):
                fail(errors, f"curated case {item.get('public_number')} has invalid image media arrays")
            for path_value in paths:
                path = ROOT / str(path_value)
                if path.exists() and (not path.is_file() or path.stat().st_size == 0):
                    fail(errors, f"curated case {item.get('public_number')} missing image asset {path_value}")
        else:
            fail(errors, f"curated case {item.get('public_number')} media_type must be image or video")
    decision_counts = data.get("decision_counts", {})
    if sum(decision_counts.values()) != data.get("total_candidates_reviewed"):
        fail(errors, "semantic review decision counts do not reconcile to total_candidates_reviewed")
    if decision_counts.get("high_confidence_update") != len(expected):
        fail(errors, "semantic review selected count differs from public case count")
    if set(data.get("selected_source_urls", [])) != {item["source_url"] for item in expected}:
        fail(errors, "semantic review selected URLs differ from curated public subset")
    if (ROOT / "README_en.md").exists():
        fail(errors, "README_en.md must not exist")
    actual_names = {path.name for path in ROOT.glob("README*.md")}
    if actual_names != set(LANGS):
        fail(errors, f"README set mismatch: {sorted(actual_names ^ set(LANGS))}")

    banner_hashes: set[str] = set()
    for banner in LANGS.values():
        banner_path = ROOT / banner
        if not banner_path.is_file():
            fail(errors, f"missing banner file {banner}")
            continue
        if png_dimensions(banner_path) != (1520, 760):
            fail(errors, f"{banner}: expected a 1520x760 PNG")
        banner_hashes.add(hashlib.sha256(banner_path.read_bytes()).hexdigest())
    if len(banner_hashes) != len(LANGS):
        fail(errors, "localized banners must have 11 distinct file hashes")
    supporting_media = {
        "images/banner-template.png": (1520, 760),
    }
    for media, expected_dimensions in supporting_media.items():
        media_path = ROOT / media
        if not media_path.is_file() or png_dimensions(media_path) != expected_dimensions:
            fail(errors, f"{media}: missing or does not match {expected_dimensions[0]}x{expected_dimensions[1]}")
    for generator in ("scripts/localize_banners.sh", "scripts/localize_banners.swift"):
        if not (ROOT / generator).is_file():
            fail(errors, f"missing deterministic banner generator {generator}")
    if manifest_path.is_file():
        expected_media = set(LANGS.values()) | {"images/banner-template.png"}
        for item in expected:
            if item["media_type"] == "video":
                expected_media.update((item["poster_path"], item["playable_video_path"]))
            else:
                expected_media.update(item["media_paths"])
        if set(remote_media) != expected_media:
            fail(errors, f"media manifest must contain all {len(expected_media)} public media assets")
        expected_prefix = "https://pub-62cf7640cd0f4066b60933bd2e9b85ef.r2.dev/github-repo-media/awesome-gpt-5.6-usecases/"
        for source, url in remote_media.items():
            local_required = source.startswith("images/")
            if not url.startswith(expected_prefix) or (local_required and not (ROOT / source).is_file()):
                fail(errors, f"invalid media manifest entry: {source}")

    english_records: list[dict[str, str | int]] = []
    for filename, banner in LANGS.items():
        path = ROOT / filename
        text = path.read_text(encoding="utf-8")
        for marker in BAD_MARKERS:
            if marker in text:
                fail(errors, f"{filename}: unresolved marker {marker}")
        expected_banner_src = remote_media.get(banner, banner)
        if f'src="{expected_banner_src}"' not in text or 'width="760"' not in text:
            fail(errors, f"{filename}: incorrect banner reference")
        if not (ROOT / banner).is_file():
            fail(errors, f"{filename}: missing banner file {banner}")
        badge_positions = [text.find(token) for token in CANONICAL_BADGES]
        if any(position < 0 for position in badge_positions) or badge_positions != sorted(badge_positions):
            fail(errors, f"{filename}: canonical language badge block missing or out of order")
        if text.find("License-CC_BY_4.0") > text.find("Try_it_on-Evolink"):
            fail(errors, f"{filename}: License badge must precede EvoLink badges")
        required_availability_markers = (
            "GPT--5.6-Available_Now",
            QUICKSTART_URL,
            "gpt-5.6-sol",
            "gpt-5.6-terra",
            "gpt-5.6-luna",
        )
        for marker in required_availability_markers:
            if marker not in text:
                fail(errors, f"{filename}: missing current GPT-5.6 availability marker {marker}")
        for anchor in CATEGORY_ANCHORS:
            if f'<a id="{anchor}"></a>' not in text or f"](#{anchor})" not in text:
                fail(errors, f"{filename}: missing category anchor or Menu link {anchor}")
        records = case_records(text)
        numbers = [record["number"] for record in records]
        if numbers != list(range(1, expected_count + 1)):
            fail(errors, f"{filename}: case numbers are not contiguous 1-{expected_count}: {numbers}")
        if any(f"](#case-{number})" not in text for number in range(1, expected_count + 1)):
            fail(errors, f"{filename}: Menu lacks one or more case links")
        for record, item in zip(records, expected):
            media = str(record["media"])
            number = item["public_number"]
            if item["media_type"] == "video":
                expected_tag = (
                    f'<a href="{item["playable_video_url"]}"><img src="{item["poster_url"]}" '
                    f'alt="Case {number} video poster" height="360"></a>'
                )
                if expected_tag not in media:
                    fail(errors, f"{filename}: case {number} video poster must use height 360")
            else:
                urls = item["r2_media_urls"]
                if len(urls) == 1:
                    expected_tag = f'<img src="{urls[0]}" alt="Case {number} source media" height="360">'
                    if expected_tag not in media or "<table>" in media:
                        fail(errors, f"{filename}: case {number} single image must use height 360 without a table")
                else:
                    if media.count("<table>") != 1 or media.count("<tr>") != ceil(len(urls) / 2):
                        fail(errors, f"{filename}: case {number} multi-image media must use two-column rows")
                    for index, url in enumerate(urls, start=1):
                        expected_tag = (
                            f'<td align="center"><img src="{url}" alt="Case {number} source media {index}" '
                            f'height="240"></td>'
                        )
                        if expected_tag not in media:
                            fail(errors, f"{filename}: case {number} image {index} must use height 240")
            if 'width="760"' in media:
                fail(errors, f"{filename}: case {number} media must not use the full-width 760 setting")
        acknowledge = text.split("## 🙏", 1)[-1]
        if re.search(r"^- \[@", acknowledge, re.MULTILINE):
            fail(errors, f"{filename}: Acknowledge creators must be comma-separated, not one bullet per creator")
        if filename == "README.md":
            stale_copy = ("early access", "coming soon", "when it becomes available", "gpt-5.5 example")
            for marker in stale_copy:
                if marker in text.lower():
                    fail(errors, f"README.md: stale availability copy remains: {marker}")
            if REFERENCE_URL not in text:
                fail(errors, "README.md: missing current GPT-5.6 complete API reference")
            headings = ["## 🍌 Introduction", "## 📊 Overview", "## ⚡ Quick Start", "## 📑 Menu", "## 💻 Coding & Builds", "## Use Cases", "## Related Repositories", "## 🙏 Acknowledge"]
            positions = [text.find(heading) for heading in headings]
            if any(position < 0 for position in positions) or positions != sorted(positions):
                fail(errors, "README.md: required section order failed")
            english_records = records
        else:
            for source, localized in zip(english_records, records):
                for field in ("source", "author", "author_url", "type", "date"):
                    if localized[field] != source[field]:
                        fail(errors, f"{filename}: case {source['number']} {field} differs from English")
                for field in ("title", "takeaway", "body"):
                    if localized[field] == source[field]:
                        fail(errors, f"{filename}: case {source['number']} {field} is unchanged from English")

    if len(english_records) == len(expected):
        for record, item in zip(english_records, expected):
            checks = {
                "number": item["public_number"], "title": item["title"], "source": item["source_url"],
                "author": item["author_handle"], "author_url": item["author_url"], "takeaway": item["takeaway"],
                "body": item["body_notes"], "type": item["type"], "date": item["date"],
            }
            for field, value in checks.items():
                if record[field] != value:
                    fail(errors, f"README/data mismatch: case {item['public_number']} {field}")
    else:
        fail(errors, "README/data case count mismatch")

    maintenance = (ROOT / "docs" / "maintenance.md").read_text(encoding="utf-8")
    for phrase in ("Source Of Truth", "Case Contract", "Update Checklist", "Validation", "Related Repositories"):
        if phrase not in maintenance:
            fail(errors, f"docs/maintenance.md missing {phrase}")
    pr = (ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
    for phrase in ("Case Metadata", "localized README", "R2", "verify_repository.py", "skill-release-agent"):
        if phrase not in pr:
            fail(errors, f"pull request template missing {phrase}")
    public_files = list(ROOT.glob("README*.md")) + list((ROOT / "docs").glob("*.md")) + [ROOT / "CONTRIBUTING.md"]
    for path in public_files:
        public_text = path.read_text(encoding="utf-8")
        if "/Users/" in public_text:
            fail(errors, f"{path.relative_to(ROOT)} exposes a user-specific absolute path")
        if ".codex/" in public_text:
            fail(errors, f"{path.relative_to(ROOT)} references unpublished internal evidence")
    for path in ROOT.rglob("*"):
        if path.name in {".DS_Store", "__pycache__"} or path.suffix == ".pyc":
            fail(errors, f"unexpected system/cache file: {path.relative_to(ROOT)}")
    return errors


def main() -> int:
    errors = verify()
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS")
    print("readmes=11")
    data = json.loads((ROOT / "data" / "gpt-5.6-usecase-curated.json").read_text(encoding="utf-8"))
    print(f"public_cases={len(data['items'])}")
    print("structured_data_equality=passed")
    print("recurring_update_handoff_fields=passed")
    print("semantic_review_reconciliation=passed")
    print("localized_case_parity=passed")
    print("localized_banner_integrity=passed")
    print("maintenance_and_pr_template=passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
