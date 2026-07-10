#!/usr/bin/env python3
"""Build the curated GPT-5.6 usecase repository from a fixed source export."""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUN_ID = "20260710-gpt56-first-publication"
EVIDENCE = REPO / ".codex" / "model-repo-pipeline" / "runs" / RUN_ID
REPO_SLUG = "awesome-gpt-5.6-usecases"
REPO_OWNER = "Evolink-AI"
MODEL = "GPT-5.6"
MODEL_URL = "https://evolink.ai/gpt-5-6"
KEYS_URL = "https://evolink.ai/dashboard/keys"
OPENAI_URL = "https://openai.com/index/previewing-gpt-5-6-sol/"

LANGUAGES = {
    "en": ("README.md", "en.png", "en"),
    "es": ("README_es.md", "es.png", "es"),
    "pt": ("README_pt.md", "pt.png", "pt"),
    "ja": ("README_ja.md", "ja.png", "ja"),
    "ko": ("README_ko.md", "ko.png", "ko"),
    "de": ("README_de.md", "de.png", "de"),
    "fr": ("README_fr.md", "fr.png", "fr"),
    "tr": ("README_tr.md", "tr.png", "tr"),
    "zh-TW": ("README_zh-TW.md", "zh-tw.png", "zh-TW"),
    "zh-CN": ("README_zh-CN.md", "zh.png", "zh-CN"),
    "ru": ("README_ru.md", "ru.png", "ru"),
}

BADGES = """[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](LICENSE)
[![Try it on Evolink](https://img.shields.io/badge/Try_it_on-Evolink-black)]({badge_url})
[![GPT-5.6 Early Access](https://img.shields.io/badge/GPT--5.6-Early_Access-f97316)]({badge_url})

[![🇺🇸 English](https://img.shields.io/badge/🇺🇸_English-Default_Source-111111)](README.md)
[![🇪🇸 Español](https://img.shields.io/badge/🇪🇸_Español-Ver-ffb703)](README_es.md)
[![🇵🇹 Português](https://img.shields.io/badge/🇵🇹_Português-Ver-2a9d8f)](README_pt.md)
[![🇯🇵 日本語](https://img.shields.io/badge/🇯🇵_日本語-表示-52b788)](README_ja.md)
[![🇰🇷 한국어](https://img.shields.io/badge/🇰🇷_한국어-보기-4ea8de)](README_ko.md)
[![🇩🇪 Deutsch](https://img.shields.io/badge/🇩🇪_Deutsch-Ansehen-f4a261)](README_de.md)
[![🇫🇷 Français](https://img.shields.io/badge/🇫🇷_Français-Voir-e76f51)](README_fr.md)
[![🇹🇷 Türkçe](https://img.shields.io/badge/🇹🇷_Türkçe-Görüntüle-d62828)](README_tr.md)
[![🇹🇼 繁體中文](https://img.shields.io/badge/🇹🇼_繁體中文-查看-8338ec)](README_zh-TW.md)
[![🇨🇳 简体中文](https://img.shields.io/badge/🇨🇳_简体中文-查看-ef476f)](README_zh-CN.md)
[![🇷🇺 Русский](https://img.shields.io/badge/🇷🇺_Русский-Смотреть-577590)](README_ru.md)"""

CATEGORIES = [
    ("coding", "Coding & Builds", "coding-and-builds", "💻"),
    ("agents", "Agents & Workflows", "agents-and-workflows", "🤖"),
    ("creative", "Creative & Product Work", "creative-and-product-work", "🎨"),
    ("evaluation", "Evaluation & Limits", "evaluation-and-limits", "🧪"),
]

CASE_SPECS = [
    {
        "url": "https://x.com/skirano/status/2075283308276220011",
        "title": "Train a Personal Model From iMessage",
        "takeaway": "Use GPT-5.6 to build and run a local training pipeline that learns a personal writing style from private message history.",
        "body_notes": "The creator reports that one prompt produced the full training pipeline, trained a model locally on a Mac from iMessage history, and generated replies in the creator's style.",
        "type": "Demo", "category": "coding",
        "reason": "Concrete end-to-end local training workflow with a stated data source, environment, and output.",
    },
    {
        "url": "https://x.com/mattshumer_/status/2075268746315268138",
        "title": "Run a Week-Long Voxel Manhattan Build",
        "takeaway": "Give a long-running coding agent a voxel Manhattan build and let it work autonomously over multiple days.",
        "body_notes": "The creator says GPT-5.6 Sol produced a detailed voxel Manhattan in a single autonomous run that lasted almost a week.",
        "type": "Demo", "category": "coding",
        "reason": "Specific long-horizon build with a named output and an explicit run duration.",
    },
    {
        "url": "https://x.com/OpenAIDevs/status/2075279941906936035",
        "title": "Turn a Spoken Spec Into a Service",
        "takeaway": "Turn a spoken natural-language specification into an end-to-end service build.",
        "body_notes": "OpenAI Developers highlights Ramp engineer Sam Kronick using GPT-5.6 to build an entire service from a natural-language specification.",
        "type": "Demo", "category": "coding",
        "reason": "Named practitioner, clear input boundary, and a concrete end-to-end software output.",
    },
    {
        "url": "https://x.com/gregisenberg/status/2075278451116818795",
        "title": "Build a Personal Business Operating System",
        "takeaway": "Start with one repetitive task, grant Codex access to the relevant tools, and expand the workflow after it works reliably.",
        "body_notes": "The 49-minute masterclass describes inbox cards with drafted replies, a unified Slack and meeting feed, an agent email address, learned repeatable skills, and goals that run for up to 20 hours.",
        "type": "Tutorial", "category": "agents",
        "reason": "Detailed multi-step workflow, concrete integrations, operating advice, and a full tutorial source.",
    },
    {
        "url": "https://x.com/AdamHoltererer/status/2075338169000620322",
        "title": "Add an Autonomous Critique Pass",
        "takeaway": "Use a second agent as a critique pass when reviewing GPT-5.6's own work.",
        "body_notes": "The creator reports that GPT-5.6 autonomously started another agent to critique its work even though no skill or instruction explicitly requested that behavior.",
        "type": "Demo", "category": "agents",
        "reason": "Concrete observed agent behavior with an explicit absence of preconfigured critique instructions.",
    },
    {
        "url": "https://x.com/clairevo/status/2075279502331248746",
        "title": "Edit a Hype Video From One Instruction",
        "takeaway": "Drop an MP4 into the workspace and request a concise promotional cut in natural language.",
        "body_notes": "The creator demonstrates the workflow from an MP4 to a 60-second hype video and links a full YouTube tutorial.",
        "type": "Tutorial", "category": "creative",
        "reason": "Clear input, instruction, output duration, and linked tutorial.",
    },
    {
        "url": "https://x.com/Creatify_AI/status/2075281407887409569",
        "title": "Produce Brand-Aware Ads Through MCP",
        "takeaway": "Connect GPT-5.6 to an ad-production MCP so the agent can use brand context, video tools, and reusable skills in one workflow.",
        "body_notes": "Creatify says its MCP lets an agent move from an idea to a finished ad in minutes with access to the full ad stack.",
        "type": "Integration", "category": "creative",
        "reason": "Named integration with an explicit tool boundary, retained brand context, and a concrete finished-ad output.",
    },
    {
        "url": "https://x.com/figma/status/2075272590822625405",
        "title": "Extend Existing Designs in Figma Make",
        "takeaway": "Use GPT-5.6 in Figma Make when building from an existing design, then compare output strength and token efficiency.",
        "body_notes": "Figma reports early tests with stronger outputs from existing designs and improved token efficiency.",
        "type": "Integration", "category": "creative",
        "reason": "First-party product integration with a specific existing-design workflow and stated test observations.",
    },
    {
        "url": "https://x.com/ArtificialAnlys/status/2075268970492657905",
        "title": "Compare Intelligence, Coding, and Cost",
        "takeaway": "Use third-party benchmark results to choose Sol, Terra, or Luna by intelligence, coding performance, and cost per task.",
        "body_notes": "Artificial Analysis reports Sol at 59 on its Intelligence Index and 80 on its Coding Agent Index; Terra and Luna score 55 and 51 on intelligence at lower cost per task. These are third-party benchmark claims from the source.",
        "type": "Benchmark", "category": "evaluation",
        "reason": "Independent pre-release evaluation with named indexes, model tiers, scores, and cost-per-task comparisons.",
    },
    {
        "url": "https://x.com/atomic_chat_hq/status/2075323372574068947",
        "title": "Test Physics Quality Against Cost",
        "takeaway": "Benchmark visual polish and physical correctness separately before choosing Sol Ultra for browser-based simulations.",
        "body_notes": "Atomic Chat compared four models on three HTML5 canvas physics scenes. It reports Sol Ultra used 32.9K tokens at $0.33 versus GPT-5.5 at 12.4K tokens and $0.11, with weaker physics despite greater visual detail.",
        "type": "Evaluation", "category": "evaluation",
        "reason": "Reproducible comparison setup with shared task prompts, token counts, costs, and a stated negative result.",
    },
]


def tracked(url: str, medium: str, content: str) -> str:
    query = urllib.parse.urlencode({
        "utm_source": "github",
        "utm_medium": medium,
        "utm_campaign": REPO_SLUG,
        "utm_content": content,
    })
    return f"{url}?{query}"


def load_candidates(source: Path) -> tuple[dict[str, dict], dict]:
    data = json.loads(source.read_text(encoding="utf-8"))
    records = list(data.get("items", []))
    for category in data.get("category_summary", {}).values():
        records.extend(category.get("representative_posts", []))
    unique: dict[str, dict] = {}
    for record in records:
        url = record.get("url", "").strip()
        if url:
            unique[url] = record
    return dict(sorted(unique.items())), data


def drop_reason(text: str, url: str) -> tuple[str, str]:
    low = text.lower()
    if "creatify" in low:
        return "drop", "already_covered"
    if any(token in low for token in ("polymarket", "crypto trades", "stocks", "market")):
        return "drop", "off_brand"
    if any(token in low for token in ("rumor", "rumour", "leak", "scoop", "waiting for", "when is", "release day", "happy gpt")):
        return "drop", "insufficient_source"
    concrete = ("built", "build", "workflow", "tutorial", "benchmark", "scores", "available in", "integration", "using gpt", "used gpt", "tested", "creates", "editing")
    if any(token in low for token in concrete):
        return "deferred", "potential_case_needs_deeper_source_extraction"
    if any(token in low for token in ("launched", "launches", "is here", "is live", "rolling out", "coming")):
        return "drop", "commentary_only"
    return "unsure", "insufficient_workflow_detail"


def build_cases(candidates: dict[str, dict]) -> list[dict]:
    cases = []
    for number, spec in enumerate(CASE_SPECS, start=1):
        source = candidates.get(spec["url"])
        if not source:
            raise SystemExit(f"selected source missing from input: {spec['url']}")
        author = source["author"].lstrip("@")
        category = next(item[1] for item in CATEGORIES if item[0] == spec["category"])
        cases.append({
            "public_number": number,
            "dedup_key": spec["url"],
            "source_url": spec["url"],
            "author_url": f"https://x.com/{author}",
            "author_handle": f"@{author}",
            "title": spec["title"],
            "takeaway": spec["takeaway"],
            "body_notes": spec["body_notes"],
            "type": spec["type"],
            "date": source["created_at_iso"][:10],
            "category": category,
            "category_key": spec["category"],
            "decision": "high_confidence_update",
            "decision_reason": spec["reason"],
            "quality_tier": "high",
            "prompt_boundary": "No exact reusable prompt text is present in the supplied JSON; omit the prompt block.",
            "prompt_public": False,
            "prompt_text": "",
            "media_type": "none",
            "source_engagement": {
                key: source.get(key, 0)
                for key in ("like_count", "view_count", "bookmark_count", "retweet_count")
            },
        })
    return cases


def build_review(candidates: dict[str, dict], cases: list[dict], source: Path) -> dict:
    selected = {case["source_url"]: case for case in cases}
    items = []
    for url, record in candidates.items():
        if url in selected:
            decision, reason = "high_confidence_update", selected[url]["decision_reason"]
        else:
            decision, reason = drop_reason(record.get("text", ""), url)
        items.append({
            "source_url": url,
            "author_handle": f"@{record.get('author', '').lstrip('@')}",
            "date": record.get("created_at_iso", "")[:10],
            "like_count": record.get("like_count", 0),
            "decision": decision,
            "reason": reason,
            "source_text": record.get("text", ""),
        })
    counts = Counter(item["decision"] for item in items)
    return {
        "run_id": RUN_ID,
        "source_artifact": str(source.resolve()),
        "collector_timestamp": "2026-07-10T06:37:00.111524+00:00",
        "candidate_count": len(items),
        "counts": dict(sorted(counts.items())),
        "selected_source_urls": [case["source_url"] for case in cases],
        "items": items,
    }


def translatable_strings(cases: list[dict]) -> list[str]:
    strings = [
        "Introduction", "Overview", "Quick Start", "Menu", "Related Repositories", "Acknowledge",
        "Coding & Builds", "Agents & Workflows", "Creative & Product Work", "Evaluation & Limits",
        "Section", "Cases", "Case", "What it shows", "Type", "Credits and correction policy",
        "Welcome to the GPT-5.6 high-signal usecase repository.",
        "We collect real-world workflows, tutorials, integrations, evaluations, and limits for GPT-5.6, curated from public evidence.",
        "Every public case in this repository comes from the supplied launch-window dataset. Case titles link to the original posts and author handles link to creator profiles.",
        "Join GPT-5.6 early access on EvoLink.",
        "10 selected GPT-5.6 cases from public creators, developers, product teams, and benchmark groups.",
        "Covers coding builds, long-running agents, business workflows, creative production, product integrations, benchmarks, and practical limits.",
        "Each case includes the original source, creator attribution, a concise takeaway, evidence type, and publication date.",
        "Use this repository to identify practical workflows and compare strengths, costs, and limitations before choosing a GPT-5.6 tier.",
        "This collection favors concrete evidence over hype. It publishes only cases with a clear workflow, integration, benchmark method, shipped result, or explicit limitation.",
        "GPT-5.6 is listed as coming soon on EvoLink. No current-model first-run route or installable GPT-5.6 skill has been verified yet.",
        "Join early access for GPT-5.6.", "Create or manage your EvoLink API key.",
        "Return to the GPT-5.6 model page for the verified first-run route when it becomes available.",
        "Do not substitute a GPT-5.5 example as proof that GPT-5.6 is callable.",
        "No dedicated GPT-5.6 Skill or API examples repository has been verified. Future Skill and API release work is owned by the separate skill-release pipeline.",
        "This repository was inspired by the creators, developers, product teams, and benchmark groups who shared real GPT-5.6 use cases publicly.",
        "Thanks to the source creators represented in this collection:",
        "We cannot guarantee that every case is attributed to the original creator. If anything needs to be corrected, please open an issue and we will update it.",
        "Share additional evidence-backed use cases through an issue or pull request.",
    ]
    for case in cases:
        strings.extend((case["title"], case["takeaway"], case["body_notes"]))
    return list(dict.fromkeys(strings))


def translate_chunk(strings: list[str], target: str) -> dict[str, str]:
    payload = "\n".join(f'<x id="{index}"/>{value}' for index, value in enumerate(strings))
    data = urllib.parse.urlencode({"client": "gtx", "sl": "en", "tl": target, "dt": "t", "q": payload}).encode()
    request = urllib.request.Request("https://translate.googleapis.com/translate_a/single", data=data)
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)
    translated = "".join(part[0] for part in result[0])
    marker = re.compile(r'<x id="(\d+)"\s*/>')
    matches = list(marker.finditer(translated))
    if len(matches) != len(strings):
        raise RuntimeError(f"translation segment mismatch for {target}: {len(matches)} != {len(strings)}")
    output = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(translated)
        output[strings[int(match.group(1))]] = translated[match.end():end].strip()
    return output


def translations(cases: list[dict], offline: bool) -> dict[str, dict[str, str]]:
    cache_path = REPO / "data" / "localization-cache.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.is_file() else {}
    strings = translatable_strings(cases)
    for lang, (_, _, target) in LANGUAGES.items():
        if lang == "en":
            cache[lang] = {value: value for value in strings}
            continue
        lang_cache = cache.setdefault(lang, {})
        missing = [value for value in strings if not lang_cache.get(value)]
        if missing and offline:
            raise SystemExit(f"offline mode: {len(missing)} missing translations for {lang}")
        for start in range(0, len(missing), 20):
            lang_cache.update(translate_chunk(missing[start:start + 20], target))
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cache


def tr(cache: dict[str, dict[str, str]], lang: str, text: str) -> str:
    return cache[lang].get(text, text)


def media_url(relative_path: str) -> str:
    manifest_path = REPO / "data" / "media-manifest.json"
    if not manifest_path.is_file():
        return relative_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest.get("files", {}).get(relative_path, relative_path)


def render_readme(lang: str, cases: list[dict], cache: dict[str, dict[str, str]]) -> str:
    filename, banner, _ = LANGUAGES[lang]
    banner_src = media_url(f"images/{banner}")
    banner_url = tracked(MODEL_URL, "banner", "readme_banner")
    badge_url = tracked(MODEL_URL, "badge", "top_badge")
    intro_url = tracked(MODEL_URL, "readme", "introduction_cta")
    model_quick = tracked(MODEL_URL, "quickstart", "model_link")
    key_url = tracked(KEYS_URL, "quickstart", "api_key")
    parts = [
        "<div align=\"center\">", "",
        f'<a href="{banner_url}"><img src="{banner_src}" alt="{MODEL} practical usecase repository banner" width="760"></a>', "",
        BADGES.format(badge_url=badge_url), "", "</div>", "",
        "# Awesome GPT-5.6 Use Cases", "",
        f"## 🍌 {tr(cache, lang, 'Introduction')}", "",
        tr(cache, lang, "Welcome to the GPT-5.6 high-signal usecase repository."), "",
        f"**{tr(cache, lang, 'We collect real-world workflows, tutorials, integrations, evaluations, and limits for GPT-5.6, curated from public evidence.')}**", "",
        tr(cache, lang, "Every public case in this repository comes from the supplied launch-window dataset. Case titles link to the original posts and author handles link to creator profiles."), "",
        f"[{tr(cache, lang, 'Join GPT-5.6 early access on EvoLink.')}]({intro_url})", "",
        f"## 📊 {tr(cache, lang, 'Overview')}", "",
        f"- **{tr(cache, lang, '10 selected GPT-5.6 cases from public creators, developers, product teams, and benchmark groups.')}**",
        f"- {tr(cache, lang, 'Covers coding builds, long-running agents, business workflows, creative production, product integrations, benchmarks, and practical limits.')}",
        f"- {tr(cache, lang, 'Each case includes the original source, creator attribution, a concise takeaway, evidence type, and publication date.')}",
        f"- {tr(cache, lang, 'Use this repository to identify practical workflows and compare strengths, costs, and limitations before choosing a GPT-5.6 tier.')}", "",
        "> [!NOTE]", f"> {tr(cache, lang, 'This collection favors concrete evidence over hype. It publishes only cases with a clear workflow, integration, benchmark method, shipped result, or explicit limitation.')}", "",
        f"## ⚡ {tr(cache, lang, 'Quick Start')}", "",
        f"**{tr(cache, lang, 'GPT-5.6 is listed as coming soon on EvoLink. No current-model first-run route or installable GPT-5.6 skill has been verified yet.')}**", "",
        f"1. [{tr(cache, lang, 'Join early access for GPT-5.6.')}]({model_quick})",
        f"2. [{tr(cache, lang, 'Create or manage your EvoLink API key.')}]({key_url})",
        f"3. [{tr(cache, lang, 'Return to the GPT-5.6 model page for the verified first-run route when it becomes available.')}]({tracked(MODEL_URL, 'docs', 'first_run')})", "",
        "```bash", 'export EVOLINK_API_KEY="your_api_key_here"', "```", "",
        f"> [!IMPORTANT]", f"> {tr(cache, lang, 'Do not substitute a GPT-5.5 example as proof that GPT-5.6 is callable.')}", "",
        f"## 📑 {tr(cache, lang, 'Menu')}", "",
        f"| {tr(cache, lang, 'Section')} | {tr(cache, lang, 'Cases')} |", "|---|---|",
    ]
    for key, label, anchor, emoji in CATEGORIES:
        cat_cases = [case for case in cases if case["category_key"] == key]
        case_range = f"Case {cat_cases[0]['public_number']}-{cat_cases[-1]['public_number']}"
        parts.append(f"| [{emoji} {tr(cache, lang, label)}](#{anchor}) | {case_range} |")
    parts.append(f"| [{tr(cache, lang, 'Acknowledge')}](#acknowledge) | {tr(cache, lang, 'Credits and correction policy')} |")
    parts.append("")
    for key, label, anchor, emoji in CATEGORIES:
        cat_cases = [case for case in cases if case["category_key"] == key]
        parts.extend([
            f"### [{emoji} {tr(cache, lang, label)}](#{anchor})", "",
            f"| {tr(cache, lang, 'Case')} | {tr(cache, lang, 'What it shows')} | {tr(cache, lang, 'Type')} |", "|---|---|---|",
        ])
        for case in cat_cases:
            parts.append(f"| [{tr(cache, lang, case['title'])}](#case-{case['public_number']}) | {tr(cache, lang, case['takeaway'])} | {case['type']} |")
        parts.append("")
    for key, label, anchor, emoji in CATEGORIES:
        parts.extend([f'<a id="{anchor}"></a>', f"## {emoji} {tr(cache, lang, label)}", ""])
        for case in [item for item in cases if item["category_key"] == key]:
            parts.extend([
                f'<a id="case-{case["public_number"]}"></a>',
                f"### Case {case['public_number']}: [{tr(cache, lang, case['title'])}]({case['source_url']}) (by [{case['author_handle']}]({case['author_url']}))", "",
                f"**{tr(cache, lang, case['takeaway'])}**", "",
                tr(cache, lang, case["body_notes"]), "",
                f"Type: {case['type']} | Date: {case['date']}", "", "---", "",
            ])
    creators = sorted({case["author_handle"] for case in cases}, key=str.lower)
    parts.extend([
        f"## {tr(cache, lang, 'Related Repositories')}", "",
        tr(cache, lang, "No dedicated GPT-5.6 Skill or API examples repository has been verified. Future Skill and API release work is owned by the separate skill-release pipeline."), "",
        f"- [OpenAI GPT-5.6 launch announcement]({OPENAI_URL})", "",
        '<a id="acknowledge"></a>', f"## 🙏 {tr(cache, lang, 'Acknowledge')}", "",
        tr(cache, lang, "This repository was inspired by the creators, developers, product teams, and benchmark groups who shared real GPT-5.6 use cases publicly."), "",
        tr(cache, lang, "Thanks to the source creators represented in this collection:"), "",
    ])
    for creator in creators:
        parts.append(f"- [{creator}](https://x.com/{creator.lstrip('@')})")
    parts.extend([
        "", f"*{tr(cache, lang, 'We cannot guarantee that every case is attributed to the original creator. If anything needs to be corrected, please open an issue and we will update it.')}*", "",
        tr(cache, lang, "Share additional evidence-backed use cases through an issue or pull request."), "",
        f"[![Star History Chart](https://api.star-history.com/svg?repos={REPO_OWNER}/{REPO_SLUG}&type=Date)](https://www.star-history.com/#{REPO_OWNER}/{REPO_SLUG}&Date)", "",
    ])
    return "\n".join(parts)


def write_support_files(cases: list[dict], review: dict, source_data: dict) -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    data_dir = REPO / "data"
    data_dir.mkdir(exist_ok=True)
    curated = {
        "repository": f"{REPO_OWNER}/{REPO_SLUG}",
        "model": MODEL,
        "source_artifact": "20260710-like-gt30-usecases-only.json",
        "source_generated_at": source_data.get("generated_at"),
        "collector_timestamp": source_data.get("collection", {}).get("collected_at"),
        "total_candidates_reviewed": review["candidate_count"],
        "total_public_cases": len(cases),
        "decision_counts": review["counts"],
        "selected_source_urls": review["selected_source_urls"],
        "public_subset_policy": "Only high-confidence source-backed workflows, integrations, benchmarks, and limits are public.",
        "items": cases,
    }
    (data_dir / "gpt-5.6-usecase-curated.json").write_text(json.dumps(curated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (data_dir / "use-cases.json").write_text(json.dumps({"items": cases}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (data_dir / "ingested_tweets.json").write_text(json.dumps([case["source_url"] for case in cases], indent=2) + "\n", encoding="utf-8")
    config = {
        "public_artifact_boundary": {"json": "public", "scripts": "public"},
        "namespace": {"heading_prefix": "Case", "anchor_prefix": "case", "section_anchor": "", "numbering_order": "document", "menu_policy": "per-case", "category_anchors": [item[2] for item in CATEGORIES]},
        "requirements": {"takeaway": True, "localized_title_translation": True},
        "structured_data": {"path": "data/gpt-5.6-usecase-curated.json", "items_key": "items"},
    }
    (data_dir / "usecase-update-config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    rows = ["# GPT-5.6 Curated Use Cases", "", "| # | Case | Type | Category | Source |", "|---:|---|---|---|---|"]
    for case in cases:
        rows.append(f"| {case['public_number']} | {case['title']} | {case['type']} | {case['category']} | [@{case['author_handle'].lstrip('@')}]({case['source_url']}) |")
    rows.extend(["", f"Source candidates reviewed: {review['candidate_count']}", f"Public cases selected: {len(cases)}", ""])
    (REPO / "gpt-5.6-usecase-curated.md").write_text("\n".join(rows), encoding="utf-8")
    (EVIDENCE / "semantic-review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = review["counts"]
    review_md = [
        "# Semantic Review", "", f"- Run id: `{RUN_ID}`", f"- Candidates: {review['candidate_count']}",
        f"- Selected: {counts.get('high_confidence_update', 0)}", f"- Deferred: {counts.get('deferred', 0)}",
        f"- Unsure: {counts.get('unsure', 0)}", f"- Dropped: {counts.get('drop', 0)}", "",
        "Only the 10 high-confidence records enter public README files. Deferred and unsure records require deeper source extraction; dropped records retain a reason class in `semantic-review.json`.", "",
    ]
    (EVIDENCE / "semantic-review.md").write_text("\n".join(review_md), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    candidates, source_data = load_candidates(args.source.expanduser().resolve())
    cases = build_cases(candidates)
    review = build_review(candidates, cases, args.source)
    write_support_files(cases, review, source_data)
    cache = translations(cases, args.offline)
    for lang, (filename, _, _) in LANGUAGES.items():
        (REPO / filename).write_text(render_readme(lang, cases, cache), encoding="utf-8")
    print(f"candidate_count={len(candidates)}")
    print(f"public_case_count={len(cases)}")
    print(f"localized_readmes={len(LANGUAGES)}")
    print(f"generated_at={datetime.now(timezone.utc).isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
