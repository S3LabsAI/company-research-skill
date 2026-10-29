#!/usr/bin/env python3
"""
Account Research Report PDF generator.

Usage:
    python3 generate_report.py input.json output.pdf     validate, then render
    python3 generate_report.py input.json --check        validate only

Input JSON: see references/data-schema.md. Older JSON files from the previous
version of this skill still render; the new fields are optional.
"""

import json
import os
import re
import sys
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    CondPageBreak, HRFlowable, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

# ---------------------------------------------------------------------------
# Fonts: use DejaVu Sans when available so names with accents or non-Latin
# characters render; fall back to Helvetica otherwise.
# ---------------------------------------------------------------------------
FONT, FONT_BOLD = 'Helvetica', 'Helvetica-Bold'
_FONT_DIRS = [
    '/usr/share/fonts/truetype/dejavu',
    '/usr/share/fonts/dejavu',
    '/Library/Fonts',
    os.path.expanduser('~/Library/Fonts'),
]
for _d in _FONT_DIRS:
    _reg, _bold = os.path.join(_d, 'DejaVuSans.ttf'), os.path.join(_d, 'DejaVuSans-Bold.ttf')
    if os.path.exists(_reg) and os.path.exists(_bold):
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', _reg))
            pdfmetrics.registerFont(TTFont('DejaVu-Bold', _bold))
            pdfmetrics.registerFontFamily('DejaVu', normal='DejaVu', bold='DejaVu-Bold',
                                          italic='DejaVu', boldItalic='DejaVu-Bold')
            FONT, FONT_BOLD = 'DejaVu', 'DejaVu-Bold'
        except Exception:
            pass
        break

C = {
    'ink': colors.HexColor('#0f172a'),
    'text': colors.HexColor('#334155'),
    'muted': colors.HexColor('#64748b'),
    'faint': colors.HexColor('#94a3b8'),
    'accent': colors.HexColor('#2563eb'),
    'accent_soft': colors.HexColor('#eff6ff'),
    'green': colors.HexColor('#059669'),
    'amber': colors.HexColor('#d97706'),
    'violet': colors.HexColor('#7c3aed'),
    'teal': colors.HexColor('#0d9488'),
    'rose': colors.HexColor('#e11d48'),
    'bg': colors.HexColor('#f8fafc'),
    'border': colors.HexColor('#e2e8f0'),
    'white': colors.white,
}

PAGE_W = 7.5 * inch  # letter width minus 0.5in margins

FRAME_LABELS = {
    'prospect': {
        'kicker': 'ACCOUNT RESEARCH REPORT  |  PROSPECT',
        'signals': 'Buying Signals',
        'use_cases': 'Use Cases & Pain Points',
        'outreach': 'Outreach Angles',
        'partners': 'Partnership Targets',
    },
    'client': {
        'kicker': 'ACCOUNT RESEARCH REPORT  |  CLIENT',
        'signals': 'Account Signals',
        'use_cases': 'Why They Bought & Pain Points',
        'outreach': 'Relationship Angles',
        'partners': 'Integrations & Tooling',
    },
}

CITE_RE = re.compile(r'\[(\d+(?:\s*[,–-]\s*\d+)*)\]')
PLACEHOLDER_RE = re.compile(r'\b(not publicly available|unknown|n/?a|tbd)\b', re.I)


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
def _ids_in(token):
    """'3, 5-7' -> [3, 5, 6, 7]"""
    ids = []
    for part in re.split(r'\s*,\s*', token):
        rng = re.split(r'\s*[–-]\s*', part)
        if len(rng) == 2 and rng[0].isdigit() and rng[1].isdigit():
            a, b = int(rng[0]), int(rng[1])
            ids.extend(range(min(a, b), max(a, b) + 1))
        elif part.strip().isdigit():
            ids.append(int(part))
    return ids


def rich(text, linkable=frozenset()):
    """Escape user text for reportlab and turn [n] citations into small
    superscript links to the matching source entry."""
    if text is None:
        return ''
    s = escape(str(text))

    def _cite(m):
        ids = _ids_in(m.group(1))
        if ids and ids[0] in linkable:
            return (f'<super><font size="6.5" color="#2563eb">'
                    f'<a href="#src{ids[0]}">[{m.group(1)}]</a></font></super>')
        return f'<super><font size="6.5" color="#64748b">[{m.group(1)}]</font></super>'

    return CITE_RE.sub(_cite, s)


def cited_ids(obj):
    found = set()
    if isinstance(obj, str):
        for m in CITE_RE.finditer(obj):
            found.update(_ids_in(m.group(1)))
    elif isinstance(obj, dict):
        for v in obj.values():
            found |= cited_ids(v)
    elif isinstance(obj, list):
        for v in obj:
            found |= cited_ids(v)
    return found


def today_str():
    now = datetime.now()
    return f'{now:%B} {now.day}, {now.year}'


def domain_of(url):
    return re.sub(r'^https?://(www\.)?', '', str(url or '')).rstrip('/')


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate(data):
    """Return a list of human-readable warnings. Rendering still proceeds."""
    w = []
    for key in ('company_name', 'source_url'):
        if not data.get(key):
            w.append(f'Missing required field: {key}')

    frame = data.get('frame', 'prospect')
    if frame not in FRAME_LABELS:
        w.append(f'frame "{frame}" is not "prospect" or "client"; using prospect headings')

    sources = data.get('sources') or []
    if not sources:
        w.append('No sources listed. Add the pages you relied on so claims can be checked.')
    source_ids = set()
    for i, src in enumerate(sources, 1):
        sid = src.get('id', i)
        if not isinstance(sid, int):
            w.append(f'Source "{src.get("title", i)}" needs an integer id')
            continue
        if sid in source_ids:
            w.append(f'Duplicate source id [{sid}]')
        source_ids.add(sid)
        if not src.get('url') and not src.get('title'):
            w.append(f'Source [{sid}] has neither a title nor a url')

    body = {k: v for k, v in data.items() if k not in ('sources', 'info_gaps')}
    used = cited_ids(body)
    missing = sorted(used - source_ids)
    if missing:
        w.append(f'Citations with no matching source: {", ".join(f"[{i}]" for i in missing)}')
    unused = sorted(source_ids - used)
    if unused and sources:
        w.append(f'Sources never cited in the body: {", ".join(f"[{i}]" for i in unused)}')

    kt = data.get('key_takeaways') or []
    if not kt:
        w.append('No key_takeaways. Page one is the most-read part of the report.')
    elif len(kt) > 5:
        w.append(f'{len(kt)} key_takeaways; keep it to 3-5 so page one stays scannable')
    for i, t in enumerate(kt, 1):
        if not cited_ids(t):
            w.append(f'key_takeaways #{i} has no citation')

    for i, a in enumerate(data.get('lead_gen', {}).get('outreach_angles', []) or [], 1):
        if not cited_ids(a):
            w.append(f'outreach_angles #{i} ("{a.get("title", "")}") is not tied to a cited finding')

    def _scan(obj, path):
        if isinstance(obj, str):
            if PLACEHOLDER_RE.search(obj) and len(obj) < 60:
                w.append(f'{path} reads "{obj}". Omit it and list the gap in info_gaps instead.')
            if '—' in obj:
                w.append(f'{path} contains an em dash; use a colon or comma')
        elif isinstance(obj, dict):
            for k, v in obj.items():
                _scan(v, f'{path}.{k}')
        elif isinstance(obj, list):
            for j, v in enumerate(obj):
                _scan(v, f'{path} #{j + 1}')

    for k, v in data.items():
        if k not in ('sources', 'info_gaps', 'source_url'):
            _scan(v, k)
    return w


# ---------------------------------------------------------------------------
# Styles and building blocks
# ---------------------------------------------------------------------------
def make_styles():
    ss = getSampleStyleSheet()
    def add(name, **kw):
        base = dict(fontName=FONT, fontSize=9.5, leading=13.5, textColor=C['text'],
                    alignment=TA_LEFT)
        base.update(kw)
        ss.add(ParagraphStyle(name, parent=ss['Normal'], **base))
    add('Body', spaceAfter=6)
    add('Small', fontSize=8.5, leading=12)
    add('Muted', fontSize=8.5, leading=12, textColor=C['muted'], spaceAfter=3)
    add('Section', fontName=FONT_BOLD, fontSize=13, leading=16, textColor=C['ink'],
        spaceBefore=14, spaceAfter=4)
    add('Sub', fontName=FONT_BOLD, fontSize=10, leading=13, textColor=C['ink'],
        spaceBefore=8, spaceAfter=4)
    add('ItemTitle', fontName=FONT_BOLD, fontSize=9.5, leading=13, textColor=C['ink'])
    add('ItemDesc', fontSize=9, leading=12.5)
    add('Cell', fontSize=8.5, leading=11.5)
    add('CellBold', fontName=FONT_BOLD, fontSize=8.5, leading=11.5, textColor=C['ink'])
    add('Takeaway', fontSize=9.5, leading=13.5, textColor=C['ink'])
    return ss


def section(title, st):
    # Heading and rule stay on the same page as the first block that follows.
    heading = Paragraph(escape(title), st['Section'])
    rule = HRFlowable(width='100%', thickness=1.2, color=C['border'], spaceAfter=8)
    heading.keepWithNext = rule.keepWithNext = True
    return [CondPageBreak(1.2 * inch), heading, rule]


def item_block(title, desc, accent, st, links):
    """Left-ruled block. Title and description share one cell so the block never
    splits across pages. Returned as a list: the block plus a small gap."""
    cell = []
    if title:
        cell.append(Paragraph(rich(title, links), st['ItemTitle']))
    if desc:
        if cell:
            cell.append(Spacer(1, 2))
        cell.append(Paragraph(rich(desc, links), st['ItemDesc']))
    if not cell:
        return []
    t = Table([[cell]], colWidths=[PAGE_W])
    t.setStyle(TableStyle([
        ('LINEBEFORE', (0, 0), (0, -1), 3, accent),
        ('BACKGROUND', (0, 0), (-1, -1), C['bg']),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return [t, Spacer(1, 5)]


def grid_table(header, rows, widths, st, first_col_bold=True):
    data = [[Paragraph(escape(h), st['CellBold']) for h in header]]
    for r in rows:
        data.append([Paragraph(c, st['CellBold'] if (i == 0 and first_col_bold) else st['Cell'])
                     for i, c in enumerate(r)])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C['bg']),
        ('GRID', (0, 0), (-1, -1), 0.5, C['border']),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return t


def bullets(items, color, st, links, style='Body'):
    return [Paragraph(f'<font color="{color}">•</font>&nbsp;&nbsp;{rich(i, links)}',
                      st[style]) for i in items if i]


def tags(items):
    return '&nbsp;&nbsp; '.join(
        f'<font color="#334155" backColor="#f1f5f9">&nbsp;{escape(str(k))}&nbsp;</font>'
        for k in items)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def header_block(data, st, labels):
    company = escape(data.get('company_name', 'Unknown Company'))
    date = escape(data.get('report_date') or today_str())
    site = data.get('source_url') or data.get('profile', {}).get('website', '')
    site_html = (f'<a href="{escape(site, {chr(34): "&quot;"})}" color="#cbd5e1">{escape(domain_of(site))}</a>'
                 if site else '')
    meta = f'Prepared {date}'
    if site_html:
        meta += f'&nbsp;&nbsp;|&nbsp;&nbsp;{site_html}'
    if data.get('prepared_for'):
        meta += f'&nbsp;&nbsp;|&nbsp;&nbsp;For {escape(data["prepared_for"])}'
    rows = [
        [Paragraph(f'<font color="#93c5fd" size="8">{labels["kicker"]}</font>', st['Small'])],
        [Paragraph(f'<font color="white" size="20">{company}</font>',
                   ParagraphStyle('h', parent=st['Small'], fontName=FONT_BOLD, leading=24))],
        [Paragraph(f'<font color="#cbd5e1" size="8.5">{meta}</font>', st['Small'])],
    ]
    t = Table(rows, colWidths=[PAGE_W])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C['ink']),
        ('LEFTPADDING', (0, 0), (-1, -1), 22),
        ('RIGHTPADDING', (0, 0), (-1, -1), 22),
        ('TOPPADDING', (0, 0), (-1, 0), 18),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 18),
    ]))
    return t


def takeaways_block(items, st, links):
    rows = [[Paragraph('KEY TAKEAWAYS', ParagraphStyle(
        'kt', parent=st['Small'], fontName=FONT_BOLD, textColor=C['accent'], fontSize=8.5))]]
    for i, t in enumerate(items, 1):
        rows.append([Paragraph(
            f'<font name="{FONT_BOLD}" color="#2563eb">{i}.</font>&nbsp;&nbsp;{rich(t, links)}',
            st['Takeaway'])])
    t = Table(rows, colWidths=[PAGE_W])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C['accent_soft']),
        ('LINEBEFORE', (0, 0), (0, -1), 3, C['accent']),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
    ]))
    return t


def profile_rows(profile, links):
    fields = [('Company', 'name'), ('Industry', 'industry'), ('Headquarters', 'headquarters'),
              ('Founded', 'founded'), ('Leader', 'ceo'), ('Size', 'size'),
              ('Website', 'website'), ('Funding / ownership', 'funding')]
    rows = []
    for label, key in fields:
        v = profile.get(key)
        if v:
            rows.append([escape(label), rich(v, links)])
    extra = profile.get('extra') or []
    if isinstance(extra, dict):
        extra = [{'label': k, 'value': v} for k, v in extra.items()]
    for e in extra:
        if e.get('value'):
            rows.append([escape(e.get('label', '')), rich(e['value'], links)])
    return rows


def build_story(data):
    st = make_styles()
    frame = data.get('frame', 'prospect')
    labels = FRAME_LABELS.get(frame, FRAME_LABELS['prospect'])
    sources = data.get('sources') or []
    links = frozenset(s.get('id', i) for i, s in enumerate(sources, 1))
    story = [header_block(data, st, labels), Spacer(1, 12)]

    if data.get('key_takeaways'):
        story += [takeaways_block(data['key_takeaways'], st, links), Spacer(1, 4)]

    if data.get('executive_summary'):
        story += section('Executive Summary', st)
        story.append(Paragraph(rich(data['executive_summary'], links), st['Body']))

    rows = profile_rows(data.get('profile') or {}, links)
    if rows:
        story += section('Company Profile', st)
        t = Table([[Paragraph(r[0], st['CellBold']), Paragraph(r[1], st['Cell'])] for r in rows],
                  colWidths=[1.7 * inch, PAGE_W - 1.7 * inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), C['bg']),
            ('GRID', (0, 0), (-1, -1), 0.5, C['border']),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
            ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t)

    people = data.get('key_people') or []
    if people:
        story += section('Key People', st)
        story.append(grid_table(
            ['Name', 'Title', 'Why they matter'],
            [[rich(p.get('name'), links), rich(p.get('title'), links), rich(p.get('notes'), links)]
             for p in people],
            [1.6 * inch, 1.9 * inch, PAGE_W - 3.5 * inch], st))

    signals = data.get('signals') or []
    if signals:
        story += section(labels['signals'], st)
        for s in signals:
            title = ': '.join(x for x in [s.get('date', ''), s.get('signal', '')] if x)
            story += item_block(title, s.get('implication'), C['rose'], st, links)

    products = data.get('products') or {}
    if any(products.get(k) for k in ('offerings', 'differentiators', 'tech_stack')):
        story += section('Products & Services', st)
        for o in products.get('offerings') or []:
            story += item_block(o.get('name'), o.get('description'), C['accent'], st, links)
        if products.get('differentiators'):
            story.append(Paragraph('Differentiators', st['Sub']))
            story += bullets(products['differentiators'], '#059669', st, links)
        if products.get('tech_stack'):
            story.append(Paragraph('Technology', st['Sub']))
            story.append(Paragraph('&nbsp;&nbsp;|&nbsp;&nbsp;'.join(
                f'<b>{escape(k)}:</b> {rich(v, links)}' for k, v in products['tech_stack'].items()),
                st['Small']))

    tm = data.get('target_market') or {}
    if any(tm.get(k) for k in ('segments', 'verticals', 'personas', 'business_model')):
        story += section('Target Market', st)
        if tm.get('segments'):
            story.append(Paragraph(rich(tm['segments'], links), st['Body']))
        if tm.get('verticals'):
            story.append(Paragraph('Verticals', st['Sub']))
            story.append(Paragraph(tags(tm['verticals']), st['Small']))
        if tm.get('personas'):
            story.append(Paragraph('Buyer personas', st['Sub']))
            for p in tm['personas']:
                story += item_block(p.get('title'), p.get('description'), C['violet'], st, links)
        if tm.get('business_model'):
            story.append(Paragraph('Business model', st['Sub']))
            story.append(Paragraph(rich(tm['business_model'], links), st['Body']))

    if data.get('use_cases'):
        story += section(labels['use_cases'], st)
        for uc in data['use_cases']:
            story += item_block(uc.get('title'), uc.get('description'), C['amber'], st, links)

    if data.get('competitors'):
        story += section('Competitive Landscape', st)
        story.append(grid_table(
            ['Competitor', 'Strengths', 'How the company differs'],
            [[rich(c.get('name'), links), rich(c.get('strengths'), links),
              rich(c.get('differentiation'), links)] for c in data['competitors']],
            [1.5 * inch, (PAGE_W - 1.5 * inch) / 2, (PAGE_W - 1.5 * inch) / 2], st))
    if data.get('competitive_positioning'):
        if not data.get('competitors'):
            story += section('Competitive Landscape', st)
        story.append(Paragraph('Positioning', st['Sub']))
        story.append(Paragraph(rich(data['competitive_positioning'], links), st['Body']))

    ind = data.get('industry') or {}
    if any(ind.get(k) for k in ('trends', 'opportunities', 'challenges')):
        story += section('Industry & Market', st)
        for key, title, color in (('trends', 'Trends', '#2563eb'),
                                  ('opportunities', 'Opportunities', '#059669'),
                                  ('challenges', 'Challenges', '#d97706')):
            if ind.get(key):
                story.append(Paragraph(title, st['Sub']))
                story += bullets(ind[key], color, st, links)

    if data.get('developments'):
        story += section('Recent Developments', st)
        for d in data['developments']:
            title = ': '.join(x for x in [d.get('date', ''), d.get('title', '')] if x)
            story += item_block(title, d.get('description'), C['teal'], st, links)

    lg = data.get('lead_gen') or {}
    if lg.get('outreach_angles'):
        story += section(labels['outreach'], st)
        for a in lg['outreach_angles']:
            story += item_block(a.get('title'), a.get('description'), C['accent'], st, links)
    if lg.get('partnership_targets'):
        story += section(labels['partners'], st)
        for p in lg['partnership_targets']:
            story += item_block(p.get('name'), p.get('rationale'), C['violet'], st, links)
    kw = lg.get('keywords') or {}
    if any(kw.values()):
        story += section('Prospecting Keywords', st)
        for key, title in (('primary', 'Services'), ('vertical', 'Verticals'),
                           ('technology', 'Technology'), ('pain_point', 'Pain points')):
            if kw.get(key):
                story.append(Paragraph(title, st['Sub']))
                story.append(Paragraph(tags(kw[key]), st['Small']))

    if data.get('info_gaps'):
        story += section('Information Gaps', st)
        story.append(Paragraph('Searched for but not found or not confirmed:', st['Muted']))
        story += bullets(data['info_gaps'], '#94a3b8', st, links, style='Small')

    if sources:
        story += section('Sources', st)
        for i, s in enumerate(sources, 1):
            sid = s.get('id', i)
            parts = [f'<a name="src{sid}"/><b>[{sid}]</b>&nbsp;&nbsp;{escape(s.get("title", ""))}']
            meta = ', '.join(escape(str(x)) for x in (s.get('publisher'), s.get('date')) if x)
            if meta:
                parts.append(f'<font color="#64748b">{meta}</font>')
            if s.get('url'):
                u = escape(s['url'], {'"': '&quot;'})
                parts.append(f'<a href="{u}" color="#2563eb">{escape(s["url"])}</a>')
            story.append(Paragraph('.&nbsp; '.join(parts[:2]) + ('<br/>' + parts[2] if len(parts) > 2 else ''),
                                   ParagraphStyle('src', parent=st['Small'], leftIndent=22,
                                                  firstLineIndent=-22, spaceAfter=4)))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width='100%', thickness=0.8, color=C['border'], spaceAfter=6))
    date = data.get('report_date') or today_str()
    story.append(Paragraph(
        f'Prepared from public sources{" and the account notes cited above" if frame == "client" else ""}, '
        f'current as of {escape(date)}. Statements marked as company claims are the company\'s own. '
        'Verify critical details before acting on them.', st['Muted']))
    return story


def generate_pdf(data, output_path):
    company = data.get('company_name', 'Account')

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(FONT, 7.5)
        canvas.setFillColor(C['faint'])
        canvas.drawString(0.5 * inch, 0.32 * inch, f'{company}  |  Account Research Report')
        canvas.drawRightString(8.0 * inch, 0.32 * inch, f'Page {doc.page}')
        canvas.restoreState()

    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                            topMargin=0.5 * inch, bottomMargin=0.6 * inch,
                            title=f'{company} - Account Research Report',
                            author='Claude', subject='Account Research Report')
    doc.build(build_story(data), onFirstPage=footer, onLaterPages=footer)
    return output_path


def main(argv):
    if len(argv) < 3:
        print(__doc__.strip())
        return 1
    with open(argv[1], encoding='utf-8') as f:
        data = json.load(f)
    warnings = validate(data)
    if warnings:
        print(f'{len(warnings)} warning(s):')
        for msg in warnings:
            print(f'  - {msg}')
    else:
        print('Validation passed with no warnings.')
    if argv[2] == '--check':
        return 0
    generate_pdf(data, argv[2])
    print(f'Report generated: {argv[2]}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
