#!/usr/bin/env python3
"""Generate all 44 concept HTML pages."""
import os, re

SRC = os.path.expanduser("~/workspace/aduan/duanyongping-kb/01-投资概念")
DST = os.path.expanduser("~/workspace/aduan/site/concept")
os.makedirs(DST, exist_ok=True)

CSS = """* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif; line-height: 1.8; color: #333; max-width: 720px; margin: 0 auto; padding: 24px 20px 60px; background: #fafaf9; }
.breadcrumb { font-size: 14px; color: #888; margin-bottom: 20px; }
.breadcrumb a { color: #2563eb; text-decoration: none; }
.breadcrumb a:hover { text-decoration: underline; }
h1 { font-size: 28px; font-weight: 700; margin-bottom: 16px; color: #111; }
h2 { font-size: 20px; font-weight: 600; margin: 32px 0 12px; color: #1e3a5f; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }
h3 { font-size: 17px; font-weight: 600; margin: 20px 0 8px; color: #333; }
.metadata { margin-bottom: 24px; display: flex; gap: 8px; flex-wrap: wrap; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 13px; font-weight: 500; }
.badge.category { background: #dbeafe; color: #1e40af; }
.badge.mentioned { background: #fef3c7; color: #92400e; }
.badge.date { background: #dcfce7; color: #166534; }
p { margin-bottom: 12px; }
blockquote { border-left: 3px solid #2563eb; background: #eff6ff; padding: 8px 16px; margin: 12px 0; color: #374151; font-style: italic; }
ul, ol { margin: 8px 0 16px 24px; }
li { margin-bottom: 6px; }
strong { color: #111; }
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 14px; }
th, td { border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; }
th { background: #f3f4f6; font-weight: 600; }
footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 13px; color: #999; text-align: center; }"""

TEMPLATE = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>{title} - 段永平投资概念</title>\n<style>\n{css}\n</style>\n</head>\n<body>\n<nav class="breadcrumb"><a href="../index.html">首页</a> &gt; <a href="index.html">概念</a> &gt; {title}</nav>\n<article>\n<h1>{title}</h1>\n<div class="metadata">\n<span class="badge category">{category}</span>\n<span class="badge mentioned">提及 {mentioned_count} 次</span>\n{date_badges}\n</div>\n{body_html}\n</article>\n<footer><p>内容源自段永平公开言论整理 · <a href="index.html">返回概念索引</a></p></footer>\n</body>\n</html>'

def parse_frontmatter(text):
    """Split YAML frontmatter and body."""
    text = text.strip()
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            body = parts[2].strip()
            fm = {}
            for line in fm_text.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, val = line.split(':', 1)
                    fm[key.strip()] = val.strip().strip('"').strip("'")
            return fm, body
    return {}, text

def md_to_html(text):
    """Simple markdown to HTML."""
    lines = text.split('\n')
    out = []
    in_list = None
    in_table = False
    table_data = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Skip initial H1
        if re.match(r'^# [^#]', line):
            i += 1
            continue
        
        # Collect multi-line blockquotes
        if line.strip().startswith('> '):
            quotes = []
            while i < len(lines) and lines[i].strip().startswith('> '):
                q = lines[i].strip()[2:]
                quotes.append(q)
                i += 1
            out.append('<blockquote><p>' + '<br>'.join(quotes) + '</p></blockquote>')
            continue
        
        # Table detection and collection
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                in_table = True
                table_data = []
            table_data.append(line)
            i += 1
            continue
        elif in_table:
            in_table = False
            if table_data:
                out.append('<table>')
                for ri, row in enumerate(table_data):
                    cells = [c.strip() for c in row.split('|')[1:-1]]
                    if ri == 1 and all(re.match(r'^[-:]+$', c) for c in cells):
                        continue
                    tag = 'th' if ri == 0 else 'td'
                    out.append('<tr>')
                    for cell in cells:
                        out.append(f'<{tag}>{cell}</{tag}>')
                    out.append('</tr>')
                out.append('</table>')
            table_data = []
            continue
        
        # Close list on blank or non-list
        if in_list and (line.strip() == '' or not re.match(r'^(\s*\d+\.\s|\s*[-]\s|\s*\*\s)', line)):
            out.append(f'</{in_list}>')
            in_list = None
        
        if line.strip() == '':
            out.append('')
            i += 1
            continue
        
        # ## Header
        m = re.match(r'^## (.+)', line)
        if m:
            out.append(f'<h2>{m.group(1)}</h2>')
            i += 1
            continue
        
        # ### Header
        m = re.match(r'^### (.+)', line)
        if m:
            out.append(f'<h3>{m.group(1)}</h3>')
            i += 1
            continue
        
        # Ordered list
        m = re.match(r'^(\d+)\.\s(.+)', line)
        if m:
            if in_list != 'ol':
                if in_list: out.append(f'</{in_list}>')
                out.append('<ol>')
                in_list = 'ol'
            out.append(f'<li>{m.group(2)}</li>')
            i += 1
            continue
        
        # Unordered list (- or *)
        m = re.match(r'^[-*]\s(.+)', line)
        if m:
            if in_list != 'ul':
                if in_list: out.append(f'</{in_list}>')
                out.append('<ul>')
                in_list = 'ul'
            out.append(f'<li>{m.group(1)}</li>')
            i += 1
            continue
        
        # Indented list continuation
        m = re.match(r'^\s+[-]\s(.+)', line)
        if m:
            if in_list != 'ul':
                if in_list: out.append(f'</{in_list}>')
                out.append('<ul>')
                in_list = 'ul'
            out.append(f'<li>{m.group(1)}</li>')
            i += 1
            continue
        
        # Bold in paragraph (non-list line)
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        t = re.sub(r'\[\[([^\]]+)\]\]', r'<a href="#">\1</a>', t)
        t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
        out.append(f'<p>{t}</p>')
        i += 1
    
    if in_list:
        out.append(f'</{in_list}>')
    
    return '\n'.join(out)


def process_all():
    files = sorted([f for f in os.listdir(SRC) if f.endswith('.md')])
    count = 0
    for fname in files:
        fpath = os.path.join(SRC, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            raw = f.read()
        
        fm, body = parse_frontmatter(raw)
        
        # Slug
        slug = re.sub(r'^\d+[-]?', '', os.path.splitext(fname)[0])
        
        title = fm.get('title', slug)
        category = fm.get('category', '未分类')
        mc = fm.get('mentioned_count', '0')
        fs = fm.get('first_seen', '')
        ls = fm.get('last_seen', '')
        
        db = ''
        if fs: db += f'<span class="badge date">首次: {fs}</span>'
        if ls: db += f'<span class="badge date">最近: {ls}</span>'
        
        body_html = md_to_html(body)
        
        html = TEMPLATE.format(
            title=title, css=CSS, category=category,
            mentioned_count=mc, date_badges=db, body_html=body_html
        )
        
        outpath = os.path.join(DST, f'{slug}.html')
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(html)
        count += 1
        print(f'  ✓ {slug}.html')
    
    print(f'\nGenerated {count} HTML pages.')

if __name__ == '__main__':
    process_all()
