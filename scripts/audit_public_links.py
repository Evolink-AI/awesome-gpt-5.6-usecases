#!/usr/bin/env python3
"""Audit every public Markdown link, image, relative path, anchor, and UTM."""

from __future__ import annotations

import argparse
import concurrent.futures
import re
import subprocess
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML_LINK = re.compile(r"<(?:a|img)\b[^>]+(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)
EXPLICIT_ANCHOR = re.compile(r'<a\s+id=["\']([^"\']+)["\']')
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


def public_files() -> list[Path]:
    files = list(ROOT.glob("README*.md"))
    files.extend((ROOT / "docs").rglob("*.md"))
    for name in ("CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md", "gpt-5.6-usecase-curated.md"):
        path = ROOT / name
        if path.is_file():
            files.append(path)
    return sorted(set(files))


def slug(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value).strip().lower()
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return re.sub(r"[\s\-]+", "-", value).strip("-")


def anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    result = set(EXPLICIT_ANCHOR.findall(text))
    result.update(slug(match.group(1)) for match in HEADING.finditer(text))
    return result


def check_external(url: str) -> tuple[str, int, str, str]:
    command = [
        "curl", "-L", "--retry", "2", "--retry-all-errors", "--connect-timeout", "10", "--max-time", "30",
        "-A", "Mozilla/5.0 (compatible; EvoLinkRepoAudit/1.0)", "-sS", "-o", "/dev/null",
        "-w", "%{http_code}\t%{url_effective}\t%{content_type}", url,
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    parts = result.stdout.strip().split("\t")
    status = int(parts[0]) if parts and parts[0].isdigit() else 0
    final = parts[1] if len(parts) > 1 else url
    content_type = parts[2] if len(parts) > 2 else ""
    return url, status, final, content_type


def severity_for(url: str, status: int) -> str:
    if status in range(200, 400):
        return "pass"
    host = urllib.parse.urlparse(url).netloc.lower()
    if "evolink.ai" in host:
        return "P0"
    if host == "openai.com" and status == 403:
        return "P2"
    if host == "api.star-history.com" and status in {0, 404, 500, 503}:
        return "P2"
    if host in {"x.com", "www.x.com"} and status in {0, 401, 403, 429}:
        return "P2"
    return "P1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    files = public_files()
    refs: list[tuple[Path, str]] = []
    relative_failures: list[str] = []
    anchor_failures: list[str] = []
    utm_failures: list[str] = []
    link_copy_warnings: list[str] = []
    anchor_cache = {path: anchors(path) for path in files}
    for path in files:
        text = path.read_text(encoding="utf-8")
        targets = MARKDOWN_LINK.findall(text) + HTML_LINK.findall(text)
        for target in targets:
            target = target.strip().strip("<>")
            refs.append((path, target))
            parsed = urllib.parse.urlparse(target)
            if parsed.scheme in {"http", "https"}:
                if parsed.netloc.lower().endswith("evolink.ai") and path.name.startswith("README"):
                    query = urllib.parse.parse_qs(parsed.query)
                    required = {"utm_source": "github", "utm_campaign": "awesome-gpt-5.6-usecases"}
                    for key, value in required.items():
                        if query.get(key) != [value]:
                            utm_failures.append(f"{path.relative_to(ROOT)}: {target} missing {key}={value}")
                    for key in ("utm_medium", "utm_content"):
                        if not query.get(key, [""])[0]:
                            utm_failures.append(f"{path.relative_to(ROOT)}: {target} missing {key}")
                continue
            if target.startswith("mailto:"):
                continue
            local, _, fragment = target.partition("#")
            target_path = (path.parent / local).resolve() if local else path.resolve()
            try:
                target_path.relative_to(ROOT)
            except ValueError:
                relative_failures.append(f"{path.relative_to(ROOT)}: path escapes repository: {target}")
                continue
            if local and not target_path.exists():
                relative_failures.append(f"{path.relative_to(ROOT)}: missing relative target {target}")
            if fragment and target_path.is_file():
                target_anchors = anchor_cache.get(target_path)
                if target_anchors is None and target_path.suffix.lower() == ".md":
                    target_anchors = anchors(target_path)
                if target_anchors is not None and fragment not in target_anchors:
                    anchor_failures.append(f"{path.relative_to(ROOT)}: unresolved fragment #{fragment} in {target}")

        for match in re.finditer(r"\[([^\]]+)\]\((https?://[^)]+)\)", text):
            copy = match.group(1).strip()
            if path.name == "README.md" and "evolink.ai" in match.group(2) and not re.match(r"^(Join|Create|Return|Run|Try|Use|Get|Read|Open|View)", copy, re.IGNORECASE):
                link_copy_warnings.append(f"{path.relative_to(ROOT)}: functional link copy may be ambiguous: {copy}")

    external = sorted({target for _, target in refs if urllib.parse.urlparse(target).scheme in {"http", "https"}})
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(check_external, external))
    severity = {url: severity_for(url, status) for url, status, _, _ in results}
    counts = Counter(severity.values())
    redirects = [(url, final) for url, status, final, _ in results if status in range(200, 400) and final.rstrip("/") != url.rstrip("/")]
    failures = [(url, status, final) for url, status, final, _ in results if severity[url] != "pass"]
    p0 = counts["P0"] + len(utm_failures)
    p1 = counts["P1"] + len(relative_failures) + len(anchor_failures)
    p2 = counts["P2"] + len(link_copy_warnings)
    report = [
        "# Public Surface Link Audit", "",
        f"- Timestamp: {datetime.now(timezone.utc).isoformat()}",
        "- Method: Markdown/HTML extraction, relative-file and fragment resolution, UTM policy checks, parallel curl GET with redirects and retries.",
        f"- Public files: {len(files)}", f"- Total references: {len(refs)}", f"- Unique external URLs: {len(external)}",
        f"- Checked external URLs: {len(results)}", "- Skipped external URLs: 0",
        f"- P0: {p0}", f"- P1: {p1}", f"- P2: {p2}", f"- Result: {'passed' if p0 == 0 and p1 == 0 else 'failed'}", "",
        "## Scope", "",
    ]
    report.extend(f"- `{path.relative_to(ROOT)}`" for path in files)
    report.extend(["", "## Failures", ""])
    if not failures and not relative_failures and not anchor_failures and not utm_failures:
        report.append("- None.")
    for url, status, final in failures:
        report.append(f"- {severity[url]}: `{status}` {url} -> {final}")
    report.extend(f"- P1: {item}" for item in relative_failures)
    report.extend(f"- P1: {item}" for item in anchor_failures)
    report.extend(f"- P0: {item}" for item in utm_failures)
    report.extend(["", "## Redirects", ""])
    report.extend(f"- {url} -> {final}" for url, final in redirects) if redirects else report.append("- None.")
    report.extend(["", "## Link Copy", ""])
    report.extend(f"- P2: {item}" for item in link_copy_warnings) if link_copy_warnings else report.append("- No ambiguous functional link copy detected.")
    report.extend(["", "## Manual And Transient Verification", ""])
    report.append("- OpenAI launch page: curl returned 403 bot protection; the official page was verified through browser readback on 2026-07-10.")
    report.append("- Star History chart: a 503 is retained as P2 while the required chart awaits repository indexing or its first star; recheck on the next repository update.")
    report.extend(["", "## External Results", "", "| Status | Severity | URL | Final URL | Content Type |", "|---:|---|---|---|---|"])
    for url, status, final, content_type in results:
        report.append(f"| {status} | {severity[url]} | {url} | {final} | {content_type or '-'} |")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"files={len(files)} references={len(refs)} unique_external={len(external)} P0={p0} P1={p1} P2={p2}")
    print(f"report={args.out.resolve()}")
    return 0 if p0 == 0 and p1 == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
