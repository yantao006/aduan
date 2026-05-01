#!/usr/bin/env python3
"""Generate company, person, and Stop Doing List HTML pages."""

import os
import re
import yaml
from pathlib import Path

KB_DIR = Path("/Users/yantao006/workspace/aduan/duanyongping-kb")
SITE_DIR = Path("/Users/yantao006/workspace/aduan/docs")

# ── Slug mapping ──────────────────────────────────────────────
def slugify(title):
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\u4e00-\u9fff-]', '-', slug)
    slug = re.sub(r'-{2,}', '-', slug)
    slug = slug.strip('-')
    mapping = {
        'right-business-right-people-right-price': 'right-business',
        'stop-doing-list-不为清单': 'stop-doing-list',
        '做对的事情-把事情做对': 'do-right',
        '步步高-bbk': 'bbk',
        '步步高': 'bbk',
        'oppo': 'oppo',
        'vivo': 'vivo',
        '苹果-apple': 'apple',
        '茅台-moutai': 'moutai',
        '拼多多-pdd': 'pdd',
        '网易-netease': 'netease',
        '腾讯-tencent': 'tencent',
        'ge-通用电气': 'ge',
        '富国银行-wells-fargo': 'wells-fargo',
        '巴菲特': 'buffett',
        '芒格': 'munger',
        '黄峥': 'huangzheng',
        '丁磊': 'dinglei',
        '陈明永': 'chenmingyong',
        '沈炜': 'shenwei',
        '金志江': 'jinzhijiang',
        '方三文': 'fangsanwen',
        '格雷厄姆': 'graham',
        '王石': 'wangshi',
    }
    if slug in mapping:
        return mapping[slug]
    return slug


# ── Markdown parsing ──────────────────────────────────────────
def parse_md(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    frontmatter = {}
    body = content
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if fm_match:
        try:
            frontmatter = yaml.safe_load(fm_match.group(1)) or {}
        except:
            pass
        body = content[fm_match.end():]
    return frontmatter, body


# ── Markdown → HTML ───────────────────────────────────────────
def md_to_html(md_text):
    html = md_text
    # Wiki links [[...]]
    def wiki_replacer(m):
        target = m.group(1)
        if '|' in target:
            target, display = target.split('|', 1)
        else:
            display = target
        slug = slugify(target)
        # Try to find type
        for t in ['concept', 'company', 'person', 'sdl']:
            if slug in SLUG_MAP.get(t, {}):
                url = f'{t}/{slug}.html'
                return f'<a href="{url}" class="wikilink">{display}</a>'
        return f'<span class="wikilink-missing">{display}</span>'
    html = re.sub(r'\[\[([^\]]+)\]\]', wiki_replacer, html)

    lines = html.split('\n')
    result = []
    in_blockquote = False
    in_table = False
    blockquote_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Tables
        if line.strip().startswith('|') and line.strip().endswith('|'):
            if not in_table:
                in_table = True
                result.append('<div class="table-wrapper"><table>')
            if re.match(r'^\|[\s\-:|\s]+\|$', line.strip()):
                i += 1
                continue
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            tag = 'th' if (i > 0 and lines[i-1].strip().startswith('|') and
                          re.match(r'^\|[\s\-:|\s]+\|$', lines[i-1].strip())) else 'td'
            result.append('<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>')
        else:
            if in_table:
                result.append('</table></div>')
                in_table = False
            if line.startswith('>'):
                blockquote_lines.append(re.sub(r'^>\s?', '', line))
                in_blockquote = True
            else:
                if in_blockquote:
                    result.append('<blockquote>' + '<br>'.join(blockquote_lines) + '</blockquote>')
                    blockquote_lines = []
                    in_blockquote = False
                if line.startswith('#### '):
                    result.append(f'<h4>{line[5:].strip()}</h4>')
                elif line.startswith('### '):
                    result.append(f'<h3>{line[3:].strip()}</h3>')
                elif line.startswith('## '):
                    result.append(f'<h2>{line[3:].strip()}</h2>')
                elif line.startswith('# '):
                    result.append(f'<h1>{line[2:].strip()}</h1>')
                elif line.strip() == '':
                    result.append('')
                elif re.match(r'^\d+\.\s', line):
                    result.append(f'<li>{line[line.index(" ")+1:].strip()}</li>')
                elif line.startswith('- ') or line.startswith('* '):
                    result.append(f'<li>{line[2:].strip()}</li>')
                elif line.strip().startswith('```'):
                    result.append(line)  # pass through code fences
                else:
                    line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                    line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
                    line = re.sub(r'~~(.+?)~~', r'<del>\1</del>', line)
                    line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)
                    if line.strip():
                        result.append(f'<p>{line}</p>')
                    else:
                        result.append('')
        i += 1
    if in_blockquote:
        result.append('<blockquote>' + '<br>'.join(blockquote_lines) + '</blockquote>')
    if in_table:
        result.append('</table></div>')
    return '\n'.join(result)


# ── HTML page wrapper ─────────────────────────────────────────
def page_wrapper(title, content, active_nav='', extra_head=''):
    nav_items = [
        ('index.html', '🏠 首页'),
        ('concepts.html', '📚 投资概念'),
        ('companies.html', '🏢 企业与品牌'),
        ('people.html', '👤 关键人物'),
        ('stop-doing.html', '🚫 Stop Doing List'),
        ('graph.html', '🕸️ 知识图谱'),
    ]
    nav_html = '\n'.join([
        f'<a href="{p}" class="nav-item{" active" if p == active_nav or (p != "index.html" and active_nav.startswith(p.rstrip(".html"))) else ""}">{l}</a>'
        for p, l in nav_items
    ])
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — 段永平知识库</title>
<link rel="stylesheet" href="/style.css">
{extra_head}
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a href="/" class="site-logo">段永平知识库</a>
    <span class="site-subtitle">建立对价值投资和企业经营的深度理解</span>
  </div>
</header>
<div class="layout">
  <nav class="sidebar" id="sidebar">
    <button class="sidebar-toggle" onclick="document.getElementById('sidebar').classList.toggle('open')">☰ 导航</button>
    <div class="nav-links">
      {nav_html}
    </div>
    <div class="search-box">
      <input type="text" id="sidebar-search" placeholder="搜索..." oninput="doSearch(this.value)">
      <div id="search-results"></div>
    </div>
  </nav>
  <main class="content">
{content}
  </main>
</div>
<footer class="site-footer">
  <p>段永平知识库 — 基于段永平公开演讲、博客、访谈内容整理。仅供参考学习，不构成投资建议。</p>
</footer>
<script src="/search.js"></script>
</body>
</html>'''


def write_page(filename, title, content, active_nav='', extra_head=''):
    filepath = SITE_DIR / filename
    os.makedirs(filepath.parent, exist_ok=True)
    html = page_wrapper(title, content, active_nav, extra_head)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✓ {filename}")


# ═══════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════

# -- Companies --
companies = []
company_dir = KB_DIR / "03-企业与品牌"
for md_file in sorted(company_dir.glob("*.md")):
    fm, body = parse_md(md_file)
    if fm:
        slug = slugify(fm.get('title', md_file.stem))
        companies.append({
            'title': fm.get('title', md_file.stem),
            'type': 'company',
            'category': fm.get('category', '经营企业'),
            'mentioned_count': fm.get('mentioned_count', 0),
            'relationship': fm.get('relationship', ''),
            'related_concepts': fm.get('related_concepts', []),
            'related_people': fm.get('related_people', []),
            'slug': slug,
            'body_raw': body,
            'first_seen': fm.get('first_seen', ''),
            'last_seen': fm.get('last_seen', ''),
        })

# -- People --
people = []
person_dir = KB_DIR / "04-关键人物"
for md_file in sorted(person_dir.glob("*.md")):
    fm, body = parse_md(md_file)
    if fm:
        slug = slugify(fm.get('title', md_file.stem))
        people.append({
            'title': fm.get('title', md_file.stem),
            'type': 'person',
            'category': fm.get('category', '投资导师'),
            'mentioned_count': fm.get('mentioned_count', 0),
            'relationship': fm.get('relationship', ''),
            'related_concepts': fm.get('related_concepts', []),
            'related_companies': fm.get('related_companies', []),
            'slug': slug,
            'body_raw': body,
            'first_seen': fm.get('first_seen', ''),
            'last_seen': fm.get('last_seen', ''),
        })

# -- SDL items --
sdl_items = []
sdl_dir = KB_DIR / "02-Stop-Doing-List"
for md_file in sorted(sdl_dir.glob("*.md")):
    if md_file.name == "README.md":
        continue
    fm, body = parse_md(md_file)
    if fm:
        slug = slugify(fm.get('title', md_file.stem))
        sdl_items.append({
            'title': fm.get('title', md_file.stem),
            'type': 'sdl',
            'category': 'Stop Doing List',
            'mentioned_count': fm.get('mentioned_count', 0),
            'sdl_number': fm.get('sdl_number', 0),
            'severity': fm.get('severity', ''),
            'original_sin': fm.get('original_sin', ''),
            'related_concepts': fm.get('related_concepts', []),
            'slug': slug,
            'body_raw': body,
        })

# -- SDL README --
sdl_readme_fm, sdl_readme_body = parse_md(sdl_dir / "README.md")

# Build slug map for wiki links
SLUG_MAP = {
    'concept': {},  # We don't load concepts here but wiki links can still resolve if needed
    'company': {c['slug']: c for c in companies},
    'person': {p['slug']: p for p in people},
    'sdl': {s['slug']: s for s in sdl_items},
}

# Convert body to HTML (with wiki link resolution)
for c in companies:
    c['body_html'] = md_to_html(c['body_raw'])
for p in people:
    p['body_html'] = md_to_html(p['body_raw'])
for s in sdl_items:
    s['body_html'] = md_to_html(s['body_raw'])
sdl_readme_html = md_to_html(sdl_readme_body)

print(f"\nLoaded: {len(companies)} companies, {len(people)} people, {len(sdl_items)} SDL items")
print(f"\nGenerating pages...\n")

# ═══════════════════════════════════════════════════════════════
# 1. COMPANIES INDEX
# ═══════════════════════════════════════════════════════════════
company_list = '<div class="card-grid">'
for c in companies:
    company_list += f'''
    <a href="/company/{c['slug']}.html" class="card">
      <span class="card-type company">企业</span>
      <h3>{c['title']}</h3>
      <span class="card-count">{c['mentioned_count']} 次提及</span>
      {f'<span class="card-relation">{c["relationship"]}</span>' if c.get('relationship') else ''}
    </a>'''
company_list += '</div>'

companies_page = f'''
<h1>企业与品牌</h1>
<p class="subtitle">共 {len(companies)} 家企业，段永平投资或经营相关的公司</p>
{company_list}
'''
write_page("companies.html", "企业与品牌", companies_page, active_nav='companies.html')

# ═══════════════════════════════════════════════════════════════
# 2. INDIVIDUAL COMPANY PAGES
# ═══════════════════════════════════════════════════════════════
for c in companies:
    related_html = ''
    if c.get('related_concepts'):
        related_html += '<div class="related-tags"><h4>相关概念</h4>'
        for rc in c['related_concepts']:
            rslug = slugify(rc)
            if rslug in SLUG_MAP['concept']:
                related_html += f'<a href="/concept/{rslug}.html" class="tag concept-tag">{rc}</a>'
            else:
                related_html += f'<span class="tag concept-tag">{rc}</span>'
        related_html += '</div>'
    if c.get('related_people'):
        related_html += '<div class="related-tags"><h4>相关人物</h4>'
        for rp in c['related_people']:
            rslug = slugify(rp)
            if rslug in SLUG_MAP['person']:
                related_html += f'<a href="/person/{rslug}.html" class="tag person-tag">{rp}</a>'
            else:
                related_html += f'<span class="tag person-tag">{rp}</span>'
        related_html += '</div>'

    meta_html = f'''
    <div class="page-meta">
      <span class="meta-item">📂 {c['category']}</span>
      <span class="meta-item">📊 {c['mentioned_count']} 次提及</span>
      {f'<span class="meta-item">🔗 {c["relationship"]}</span>' if c.get('relationship') else ''}
      {f'<span class="meta-item">📅 {c["first_seen"]} — {c["last_seen"]}</span>' if c.get('first_seen') else ''}
    </div>'''

    company_page = f'''
<h1>{c['title']}</h1>
{meta_html}
<div class="article-body">
  {c['body_html']}
</div>
{related_html}
'''
    write_page(f"company/{c['slug']}.html", c['title'], company_page, active_nav='companies.html')

# ═══════════════════════════════════════════════════════════════
# 3. PEOPLE INDEX
# ═══════════════════════════════════════════════════════════════
people_list = '<div class="card-grid">'
for p in people:
    people_list += f'''
    <a href="/person/{p['slug']}.html" class="card">
      <span class="card-type person">人物</span>
      <h3>{p['title']}</h3>
      <span class="card-count">{p['mentioned_count']} 次提及</span>
      {f'<span class="card-relation">{p["relationship"]}</span>' if p.get('relationship') else ''}
    </a>'''
people_list += '</div>'

people_page = f'''
<h1>关键人物</h1>
<p class="subtitle">共 {len(people)} 位关键人物，对段永平思想产生重要影响的人</p>
{people_list}
'''
write_page("people.html", "关键人物", people_page, active_nav='people.html')

# ═══════════════════════════════════════════════════════════════
# 4. INDIVIDUAL PERSON PAGES
# ═══════════════════════════════════════════════════════════════
for p in people:
    related_html = ''
    if p.get('related_concepts'):
        related_html += '<div class="related-tags"><h4>相关概念</h4>'
        for rc in p['related_concepts']:
            rslug = slugify(rc)
            if rslug in SLUG_MAP['concept']:
                related_html += f'<a href="/concept/{rslug}.html" class="tag concept-tag">{rc}</a>'
            else:
                related_html += f'<span class="tag concept-tag">{rc}</span>'
        related_html += '</div>'
    if p.get('related_companies'):
        related_html += '<div class="related-tags"><h4>相关企业</h4>'
        for rc in p['related_companies']:
            rslug = slugify(rc)
            if rslug in SLUG_MAP['company']:
                related_html += f'<a href="/company/{rslug}.html" class="tag company-tag">{rc}</a>'
            else:
                related_html += f'<span class="tag company-tag">{rc}</span>'
        related_html += '</div>'

    meta_html = f'''
    <div class="page-meta">
      <span class="meta-item">📂 {p['category']}</span>
      <span class="meta-item">📊 {p['mentioned_count']} 次提及</span>
      {f'<span class="meta-item">🔗 {p["relationship"]}</span>' if p.get('relationship') else ''}
      {f'<span class="meta-item">📅 {p["first_seen"]} — {p["last_seen"]}</span>' if p.get('first_seen') else ''}
    </div>'''

    person_page = f'''
<h1>{p['title']}</h1>
{meta_html}
<div class="article-body">
  {p['body_html']}
</div>
{related_html}
'''
    write_page(f"person/{p['slug']}.html", p['title'], person_page, active_nav='people.html')

# ═══════════════════════════════════════════════════════════════
# 5. STOP DOING LIST HUB (from README.md)
# ═══════════════════════════════════════════════════════════════
sdl_page = f'''
<h1>Stop Doing List · 不为清单</h1>
<p class="subtitle">段永平从巴菲特处学到的核心理念，加上自己的血的教训</p>

<div class="article-body">
  {sdl_readme_html}
</div>

<div class="sdl-card-grid">
  <h2>📋 不为清单条目（{len(sdl_items)} 条）</h2>
  <div class="card-grid">
'''
for s in sdl_items:
    sdl_page += f'''
    <a href="/stop-doing/{s['slug']}.html" class="card sdl-card">
      <span class="sdl-number-badge">#{s['sdl_number']}</span>
      <h3>{s['title']}</h3>
      {f'<span class="card-severity">{s["severity"]}</span>' if s.get('severity') else ''}
      <span class="card-count">{s['mentioned_count']} 次提及</span>
    </a>'''
sdl_page += '''
  </div>
</div>
'''
write_page("stop-doing.html", "Stop Doing List", sdl_page, active_nav='stop-doing.html')

# ═══════════════════════════════════════════════════════════════
# 6. INDIVIDUAL SDL CARD PAGES
# ═══════════════════════════════════════════════════════════════
for s in sdl_items:
    related_html = ''
    if s.get('related_concepts'):
        related_html += '<div class="related-tags"><h4>相关概念</h4>'
        for rc in s['related_concepts']:
            rslug = slugify(rc)
            # Check if it's an SDL item or concept
            if rslug in SLUG_MAP['sdl']:
                related_html += f'<a href="/stop-doing/{rslug}.html" class="tag sdl-tag">{rc}</a>'
            elif rslug in SLUG_MAP['concept']:
                related_html += f'<a href="/concept/{rslug}.html" class="tag concept-tag">{rc}</a>'
            else:
                related_html += f'<span class="tag">{rc}</span>'
        related_html += '</div>'

    severity_badge = ''
    if s.get('severity'):
        sev_class = s['severity'].lower()
        severity_badge = f'<span class="severity-badge severity-{sev_class}">{s["severity"]}</span>'

    original_sin_html = ''
    if s.get('original_sin'):
        original_sin_html = f'<span class="meta-item">💥 血的教训：{s["original_sin"]}</span>'

    meta_html = f'''
    <div class="page-meta sdl-meta">
      <span class="sdl-number-large">#{s['sdl_number']}</span>
      <span class="meta-item">📂 {s['category']}</span>
      <span class="meta-item">📊 {s['mentioned_count']} 次提及</span>
      {severity_badge}
      {original_sin_html}
    </div>'''

    sdl_card_page = f'''
<h1>{s['title']}</h1>
{meta_html}
<div class="article-body">
  {s['body_html']}
</div>
{related_html}
<div class="back-link">
  <a href="/stop-doing.html">← 返回 Stop Doing List</a>
</div>
'''
    write_page(f"stop-doing/{s['slug']}.html", s['title'], sdl_card_page, active_nav='stop-doing.html')

# ═══════════════════════════════════════════════════════════════
# 7. SEARCH INDEX (update with SDL individual pages)
# ═══════════════════════════════════════════════════════════════
import json

search_index = []
for item in companies:
    search_index.append({
        't': item['title'],
        'y': '企业',
        'p': f'company/{item["slug"]}.html',
        'b': item['body_raw'][:500].replace('\n', ' ').strip(),
    })
for item in people:
    search_index.append({
        't': item['title'],
        'y': '人物',
        'p': f'person/{item["slug"]}.html',
        'b': item['body_raw'][:500].replace('\n', ' ').strip(),
    })
for item in sdl_items:
    search_index.append({
        't': item['title'],
        'y': '不为清单',
        'p': f'stop-doing/{item["slug"]}.html',
        'b': item['body_raw'][:500].replace('\n', ' ').strip(),
    })
# Add SDL hub
search_index.append({
    't': 'Stop Doing List · 不为清单',
    'y': '不为清单',
    'p': 'stop-doing.html',
    'b': sdl_readme_body[:500].replace('\n', ' ').strip(),
})

with open(SITE_DIR / "search-index.json", 'w', encoding='utf-8') as f:
    json.dump(search_index, f, ensure_ascii=False)
print(f"\n  ✓ search-index.json ({len(search_index)} items)")

print(f"\n✅ Done! All pages generated in {SITE_DIR}")
