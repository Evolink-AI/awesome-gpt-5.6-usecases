# Maintenance

## Source Of Truth

- Public cases: `data/gpt-5.6-usecase-curated.json`
- Source intake metadata: `source_artifact` and `source_generated_at` in `data/gpt-5.6-usecase-curated.json`
- English structure: `README.md`
- Localization cache: `data/localization-cache.json`
- Build command: `python3 scripts/build_repository.py --curated data/gpt-5.6-usecase-curated.json --offline`

The public dataset contains only the selected high-confidence subset. It also records the aggregate review decision counts and the selected source URLs needed to reconcile the public case set.

## Case Contract

Every case requires a contiguous number, stable `case-N` anchor, source URL, author URL, English title, reader-action takeaway, source-grounded notes, allowed type, ISO date, category, decision reason, and dedup key. Do not invent prompts, results, pricing, benchmark numbers, dates, or attribution.

## Update Checklist

1. Review the current English and localized READMEs, source index, and dirty worktree state.
2. Collect candidates with a fixed collector timestamp and deduplicate by canonical source URL.
3. Classify every candidate as selected, deferred, unsure, or dropped with a reason.
4. Verify the handoff package before changing public README files.
5. Update English first and run the English gate.
6. Translate visible prose in all 10 localized README files while preserving links, anchors, type values, dates, code, model IDs, and environment variables.
7. Run the localized gate, repository verifier, media/link check, public-surface link audit, and `git diff --check`.
8. Re-audit after every P0/P1 fix. Commit and push only after owner approval.

## Validation

```bash
python3 scripts/build_repository.py --curated data/gpt-5.6-usecase-curated.json --language en --offline
python3 scripts/verify_repository.py
python3 /path/to/model-repo-pipeline/bundled-skills/usecase-update-loop/scripts/verify_usecase_update.py --repo .
git diff --check
```

## Media

The repository retains one language-path PNG banner per README, plus the canonical source template with its embedded EvoLink mark. On macOS, regenerate all language variants with `scripts/localize_banners.sh`. Before publication, inventory and upload all files in `images/` to the approved R2 namespace, record the upload result, and verify the actual GitHub-rendered image or camo URL after push. Do not add raw video embeds.

## Related Repositories

This repository only links related API or Skill surfaces. Creation, audit, release, npm publication, and API smoke tests for those surfaces belong to `skill-release-agent`.
