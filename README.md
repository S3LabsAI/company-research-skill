# company-research-skill

A packaged Claude Agent Skill that researches a company from its name or URL and
generates a cited, styled PDF "Account Research Report." It handles venture-backed
tech, mid-market firms, and local businesses such as insurance agencies.

The repository contains the source docs and the packaged skill artifact. In this
repository the artifact is currently checked in as `company-research-skill.md`;
when you distribute it to Claude, either rename it to `research-company.skill` or
export the zip archive under that name. The repo keeps the original checked-in name
so the binary artifact remains traceable in Git.

## Contents

The `research-company.skill` archive contains:

- `research-company/SKILL.md`: the skill manifest and workflow instructions.
- `research-company/references/data-schema.md`: the JSON schema the PDF generator
  reads, frame headings, citation format, and a worked example.
- `research-company/scripts/generate_report.py`: validates a JSON research file and
  renders it into a styled PDF using [reportlab](https://pypi.org/project/reportlab/).

## Features

- **Research workflow** that classifies the company type first (tech, mid-market,
  or local business) and looks where that type's facts live, including carrier
  agent pages, reviews, and license lookups for insurance agencies.
- **Citations throughout.** Claims carry inline `[n]` markers that render as
  superscript links to a numbered Sources section at the end of the report.
- **Evidence rules:** attribute company claims, date facts that change, label
  estimates, and record conflicts and missing facts in Information Gaps.
- **Page one built for skimming:** a Key Takeaways box, then the executive summary
  and company profile.
- **Two frames:** `prospect` (an account to win) and `client` (an existing
  account). The frame relabels the signals, use-case, angle, and partner sections.
- **Sections:** key takeaways, executive summary, company profile (with custom
  rows), key people, buying or account signals, products and services, target
  market, use cases, competitive landscape, industry and market, recent
  developments, outreach angles, partnership targets, prospecting keywords,
  information gaps, and sources. Empty sections are skipped.
- **Validator** that runs before every render and flags missing required fields,
  citation numbers with no matching source, uncited sources, uncited takeaways and
  outreach angles, placeholder text, and em dashes.
- **Rendering details:** escapes `&` and `<` in names, uses DejaVu Sans when it is
  installed (falls back to Helvetica), keeps section headings with their content,
  adds a page footer with page numbers, and sets PDF metadata.
- **Backward compatible:** JSON written for v1 still renders; the new fields are
  optional.

## Installation

The PDF generator requires Python 3 and reportlab:

```bash
pip install reportlab
```

`reportlab` is the only third-party import in `generate_report.py`. When the
packaged artifact is used directly in Claude, name it `research-company.skill`.
For this repo, the checked-in artifact keeps its Git-traceable file name
`company-research-skill.md` until it is exported for distribution.

## Usage

Validate a JSON file, then render it:

```bash
python3 scripts/generate_report.py input.json "Company Name - Account Research Report.pdf"
```

Validate only, without rendering:

```bash
python3 scripts/generate_report.py input.json --check
```

Running it without both arguments prints usage and exits. The input JSON follows
`references/data-schema.md`. Only `company_name` and `source_url` are required.

## Configuration

There are no environment variables or configuration files. Behavior is controlled
by the input JSON (including `frame` and `prepared_for`) and the command-line
arguments.

## Changelog

### v2 (2026-10-29)

- Added inline citations, a numbered Sources section, Key Takeaways, Key People,
  and Buying/Account Signals.
- Added `prospect` and `client` frames and company-type classification, with
  research guidance for local businesses and insurance agencies.
- Replaced the fixed four-query research step (one hardcoded to 2024) with
  topic coverage and current-year queries.
- Added the JSON validator and `--check` mode.
- Fixed PDF rendering of names containing `&` or `<`, added Unicode font support,
  page numbers, and heading orphan control.
- Rewrote the schema reference with a contents list, frame table, and a cited
  worked example.

### v1

- Initial release.

## License

No license file is included in this repository.
