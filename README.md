# Company Research Skill

A Claude skill that researches a company from its name or URL and produces a
cited, styled **Account Research Report** as a PDF. Built for salespeople and
account managers who need a page-one brief before a call and a sourced reference
afterward. It handles venture-backed tech, mid-market firms, and local businesses
such as insurance agencies.

See a sample report: [`examples/sample-report.pdf`](examples/sample-report.pdf)
(a fictional agency, rendered from [`examples/sample-data.json`](examples/sample-data.json)).

## What it does

- **Classifies the company first** (tech, mid-market or enterprise, local business)
  and researches where that type's facts actually live, including carrier agent
  pages, reviews, and license lookups for insurance agencies.
- **Cites every claim.** Inline `[n]` markers render as superscript links to a
  numbered Sources section.
- **Applies evidence rules:** attributes company claims, dates facts that change,
  labels estimates, and records conflicts and missing facts as Information Gaps.
- **Leads with what matters:** a Key Takeaways box on page one pairs each cited
  fact with why it matters to the reader.
- **Supports two frames:** `prospect` (an account to win) and `client` (an
  existing account). The frame relabels the signals, use-case, angle, and partner
  sections.
- **Validates before rendering:** flags missing required fields, citation numbers
  with no matching source, uncited sources, uncited takeaways and outreach angles,
  placeholder text, and em dashes.

## Report sections

Key takeaways, executive summary, company profile, key people, buying or account
signals, products and services, target market, use cases, competitive landscape,
industry and market, recent developments, outreach angles, partnership targets,
prospecting keywords, information gaps, and sources. Sections with no content
are skipped.

## Repository layout

```
SKILL.md                      Skill instructions and frontmatter
references/data-schema.md     JSON schema, frame headings, citation format, worked example
scripts/generate_report.py    Validates the research JSON and renders the PDF
examples/sample-data.json     Worked example input (fictional company)
examples/sample-report.pdf    PDF rendered from the sample input
requirements.txt              Python dependency (reportlab)
```

## Requirements

- Python 3.8 or later
- [reportlab](https://pypi.org/project/reportlab/)

```bash
pip install -r requirements.txt
```

Web search and page-fetch tools are needed for the research step. The PDF
step only needs Python and reportlab.

## Usage

Ask Claude to research a company, for example:

- "Research acme.com and give me an account research report."
- "Build a client account report for Harbor & Pine Insurance, we just signed them."

The skill researches the company, writes the report data as JSON, and renders it:

```bash
python3 scripts/generate_report.py report_data.json "Company Name - Account Research Report.pdf"
```

Validate a JSON file without rendering:

```bash
python3 scripts/generate_report.py report_data.json --check
```

Try it with the bundled example:

```bash
python3 scripts/generate_report.py examples/sample-data.json sample.pdf
```

## Changelog

### v2 (2026-10-29)

- Inline citations, a numbered Sources section, Key Takeaways, Key People, and
  Buying/Account Signals.
- `prospect` and `client` frames, plus company-type classification with research
  guidance for local businesses and insurance agencies.
- Topic-based research coverage with current-year queries, replacing four fixed
  queries (one hardcoded to 2024).
- JSON validator and `--check` mode.
- PDF fixes: escaping for names containing `&` or `<`, Unicode font support,
  page numbers, and section headings kept with their content.
- Schema reference rewritten with a contents list, frame table, and a cited
  worked example. JSON written for v1 still renders.

### v1

- Initial release.

## License

No license has been chosen for this repository yet.
