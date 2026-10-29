# Report Data Schema

The JSON that `scripts/generate_report.py` renders. Read this before building the data.

## Contents

1. Rules that apply to every field
2. Field reference
3. Frame headings
4. Worked example (local insurance agency, prospect frame)
5. Notes for other company types

## 1. Rules that apply to every field

- **Citations.** Put source numbers in square brackets inside any text value: `"Founded 2011 [1]"`, `"Two offices [1, 3]"`, `"[2-4]"`. Each number must match an `id` in `sources`. The PDF turns them into superscript links to the Sources list, and the validator flags numbers with no matching source.
- **Optional means omit.** Every field except `company_name` and `source_url` is optional. Leave out a field or section that doesn't apply instead of filling it with "Not publicly available" or "N/A". Record what you looked for and couldn't find in `info_gaps`.
- **Plain text only.** Write text values as plain text. The generator escapes characters such as `&` and `<`, so don't add HTML or markdown.
- **Order.** List `developments` and `signals` newest first.

## 2. Field reference

```json
{
  "company_name": "string, required",
  "source_url": "string, required: the company's primary website or profile page",
  "report_date": "string: today's date, e.g. 'March 4, 2027'. Defaults to today if omitted",
  "frame": "'prospect' (default) or 'client'. Changes several section headings, see section 3",
  "prepared_for": "string, optional: shown in the header, e.g. 'Tom Panos, GOAL'",

  "key_takeaways": ["3-5 strings. Each pairs a cited fact with why it matters to the reader"],
  "executive_summary": "string, 3-5 sentences: what they do, for whom, how big, where they stand",

  "profile": {
    "name": "string",
    "industry": "string",
    "headquarters": "string",
    "founded": "string",
    "ceo": "string: name and title of the top leader or owner",
    "size": "string with source and date, e.g. 'About 45 employees on LinkedIn, Oct 2026 [4]'",
    "website": "string",
    "funding": "string: funding, or ownership for companies that aren't venture-backed",
    "extra": [{"label": "string", "value": "string"}]
  },

  "key_people": [
    {"name": "string", "title": "string as published", "notes": "why they matter to the reader, with citation"}
  ],

  "signals": [
    {"date": "string, e.g. 'Aug 2026'", "signal": "what happened", "implication": "why it matters now"}
  ],

  "products": {
    "offerings": [{"name": "string", "description": "string"}],
    "differentiators": ["string: attribute company claims, e.g. 'Claims 24-hour claims callback [2]'"],
    "tech_stack": {"Category": "string"}
  },

  "target_market": {
    "segments": "string",
    "verticals": ["string"],
    "personas": [{"title": "string", "description": "string"}],
    "business_model": "string"
  },

  "use_cases": [{"title": "string", "description": "string"}],

  "competitors": [
    {"name": "string", "strengths": "string", "differentiation": "string: evidence-based, how the company differs"}
  ],
  "competitive_positioning": "string",

  "industry": {
    "trends": ["string, specific to the vertical and geography"],
    "opportunities": ["string"],
    "challenges": ["string"]
  },

  "developments": [
    {"date": "string", "title": "string", "description": "string: what happened and why it matters"}
  ],

  "lead_gen": {
    "outreach_angles": [{"title": "string", "description": "string tied to a cited finding, written as an inference"}],
    "partnership_targets": [{"name": "string", "rationale": "string"}],
    "keywords": {
      "primary": ["service keywords for finding lookalike accounts"],
      "vertical": ["string"],
      "technology": ["string"],
      "pain_point": ["string"]
    }
  },

  "info_gaps": ["string: what's missing and where it might live"],

  "sources": [
    {"id": 1, "title": "string", "publisher": "string", "date": "string: published or accessed", "url": "string"}
  ]
}
```

The PDF renders sections in this order: header, key takeaways, executive summary, company profile, key people, signals, products and services, target market, use cases, competitive landscape, industry and market, recent developments, outreach angles, partnership targets, prospecting keywords, information gaps, sources.

## 3. Frame headings

| Field | `prospect` heading | `client` heading and meaning |
|---|---|---|
| `signals` | Buying Signals | Account Signals: changes that affect the relationship or the campaign |
| `use_cases` | Use Cases & Pain Points | Why They Bought & Pain Points: the pains they stated during the sale |
| `lead_gen.outreach_angles` | Outreach Angles | Relationship Angles: how to run the account and what keeps them engaged |
| `lead_gen.partnership_targets` | Partnership Targets | Integrations & Tooling: CRM, lead routing, and tool preferences |

## 4. Worked example

A fictional independent agency, so every name, number, and URL below is invented. The dates are illustrative; use today's date and the real dates from your sources. Note what it leaves out: no funding, tech stack, personas, or keywords, because they don't fit a local agency.

```json
{
  "company_name": "Harbor & Pine Insurance Group",
  "source_url": "https://harborpine.example",
  "report_date": "October 29, 2026",
  "frame": "prospect",

  "key_takeaways": [
    "Opened a second office in Dublin, OH in Aug 2026 [3]: new territory to fill, so lead volume is a near-term need.",
    "Posted two producer openings in Sep 2026 [5]: they are adding capacity to work more leads, not fewer.",
    "4.8 stars across 212 Google reviews [4], with reviewers repeatedly naming fast quote turnaround: speed-to-contact is part of their brand.",
    "Ohio homeowners carriers filed average increases of about 9% for 2026 [6]: expect more rate shoppers and plan home bind rates accordingly."
  ],
  "executive_summary": "Harbor & Pine is an independent agency in Columbus, OH selling personal auto and home plus small commercial lines through 14 carrier appointments [1]. It runs two offices and lists 11 staff, including 6 licensed producers [1, 3]. The owners have grown it steadily since 2011 and are now expanding into Dublin [3]. It competes with captive agents and online carriers on service and carrier choice rather than price [1, 4].",

  "profile": {
    "name": "Harbor & Pine Insurance Group LLC [2]",
    "industry": "Independent insurance agency: personal and small commercial lines [1]",
    "headquarters": "Columbus, OH [1]",
    "founded": "2011 [2]",
    "ceo": "Dana Whitfield, Owner & Principal Agent [1]",
    "size": "11 staff listed on the team page, 6 licensed producers, Oct 2026 [1]",
    "website": "harborpine.example",
    "funding": "Privately held by its two founding partners [2]",
    "extra": [
      {"label": "Carrier appointments", "value": "14 listed, including Progressive, Travelers, and Grange [1]"},
      {"label": "Locations", "value": "Columbus (HQ) and Dublin, opened Aug 2026 [3]"},
      {"label": "Reputation", "value": "4.8 stars, 212 Google reviews, Oct 2026 [4]"}
    ]
  },

  "key_people": [
    {"name": "Dana Whitfield", "title": "Owner & Principal Agent", "notes": "Decision-maker on marketing spend; quoted in the Dublin opening coverage [1, 3]"},
    {"name": "Marcus Lee", "title": "Partner, Commercial Lines", "notes": "Co-founder; leads the commercial book [1, 2]"},
    {"name": "Priya Shah", "title": "Office Manager", "notes": "Listed as the contact for new-client intake; likely owns lead routing [1]"}
  ],

  "signals": [
    {"date": "Sep 2026", "signal": "Two licensed producer openings posted [5]", "implication": "Adding capacity ahead of growth; leads won't go unworked."},
    {"date": "Aug 2026", "signal": "Second office opened in Dublin, OH [3]", "implication": "A new territory with no book yet needs a lead source."}
  ],

  "products": {
    "offerings": [
      {"name": "Personal lines", "description": "Auto, home, renters, umbrella, and recreational vehicles [1]"},
      {"name": "Small commercial", "description": "BOP, general liability, and commercial auto for contractors and retail [1]"}
    ],
    "differentiators": [
      "Claims same-day quotes on personal lines [1]",
      "14 carrier appointments give more price options than a captive agent [1]"
    ]
  },

  "target_market": {
    "segments": "Homeowners and families in the Columbus metro, plus contractors and small retailers for commercial lines [1]",
    "verticals": ["Personal auto", "Homeowners", "Contractors", "Retail"]
  },

  "competitors": [
    {"name": "Local captive agents (State Farm, Allstate)", "strengths": "Brand recognition and national ad budgets", "differentiation": "Harbor & Pine can shop 14 carriers when a captive's rate rises [1, 6]"},
    {"name": "Online direct carriers", "strengths": "Fast self-serve quotes and low prices for simple risks", "differentiation": "Reviews credit personal service and help with claims [4]"}
  ],

  "industry": {
    "trends": ["Ohio homeowners carriers filed average increases of about 9% for 2026, pushing more households to shop [6]"],
    "challenges": ["Higher home premiums lower bind rates on home quotes even when lead quality holds [6]"]
  },

  "developments": [
    {"date": "Aug 2026", "title": "Dublin office opens", "description": "Second location staffed by two producers; the owner cited demand from northwest Columbus suburbs [3]"}
  ],

  "lead_gen": {
    "outreach_angles": [
      {"title": "Fill the new territory", "description": "The Dublin office opened in August [3] and needs a book. Lead with exclusive, ZIP-targeted volume for Dublin and the northwest suburbs."},
      {"title": "Speed matches their brand", "description": "Reviewers praise fast quotes [4]. Real-time lead delivery fits how they already sell."}
    ]
  },

  "info_gaps": [
    "Annual premium volume or revenue: private, not disclosed",
    "Current lead vendors and monthly marketing spend: not public; ask on the first call",
    "CRM or agency management system: not mentioned on the site or in job posts"
  ],

  "sources": [
    {"id": 1, "title": "About Us and Our Team", "publisher": "Harbor & Pine website", "date": "Accessed Oct 29, 2026", "url": "https://harborpine.example/about"},
    {"id": 2, "title": "Business entity record", "publisher": "Ohio Secretary of State", "date": "Accessed Oct 29, 2026", "url": "https://sos.example/harborpine"},
    {"id": 3, "title": "Harbor & Pine opens Dublin office", "publisher": "Dublin Local News", "date": "Aug 14, 2026", "url": "https://dublinnews.example/harbor-pine"},
    {"id": 4, "title": "Google Business Profile reviews", "publisher": "Google", "date": "Accessed Oct 29, 2026", "url": "https://maps.example/harborpine"},
    {"id": 5, "title": "Licensed Insurance Producer job posting", "publisher": "Indeed", "date": "Sep 22, 2026", "url": "https://jobs.example/harborpine-producer"},
    {"id": 6, "title": "2026 homeowners rate filings summary", "publisher": "Ohio Department of Insurance", "date": "Jul 2026", "url": "https://insurance.example/2026-filings"}
  ]
}
```

## 5. Notes for other company types

- **Venture-backed or tech:** fill `funding` with round, amount, lead investor, and date, add `tech_stack` when the stack is published or evident from job posts, and use `target_market.personas` for the roles that buy.
- **Mid-market or enterprise:** use `funding` for ownership (public ticker, PE owner, parent company) and add revenue to `profile.extra` when it's reported, with the period.
- **Client frame:** cite internal context such as CRM records or call notes as sources too, e.g. `{"id": 7, "title": "Won opportunity note", "publisher": "Close CRM", "date": "Jul 29, 2026"}`. A source without a URL is fine.
