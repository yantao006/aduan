#!/usr/bin/env python3
"""Extract clean markdown from 4 HTML articles about 段永平."""

from bs4 import BeautifulSoup
import html
import re
import os

INPUT_DIR = os.path.expanduser("~/workspace/duanyongping/02-supplement/web-articles")
OUTPUT_DIR = os.path.expanduser("~/workspace/duanyongping/02-supplement/web-articles-md")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── File 1: sina_fangsanwen.html ───
def convert_file1():
    print("Converting file 1: sina_fangsanwen.html")
    path = os.path.join(INPUT_DIR, "sina_fangsanwen.html")
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Title from h1
    title = soup.find("h1", class_="main-title")
    title_text = title.get_text(strip=True) if title else "2025年段永平雪球访谈完整版"

    # Date from meta or span
    date_span = soup.find("span", class_="date")
    date_raw = date_span.get_text(strip=True) if date_span else "2025-11-26"
    # Parse "2025年11月26日 11:19" -> 2025-11-26
    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_raw)
    if date_match:
        date_str = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
    else:
        date_str = "2025-11-26"

    # Source
    source_span = soup.find("span", class_="ent-source")
    source_text = source_span.get_text(strip=True) if source_span else "看点资讯"
    source_url = "https://t.cj.sina.cn/articles/view/6385226361/17c96d27900101k39y"

    # Body content: div#artibody
    body_div = soup.find("div", id="artibody")
    body_html = str(body_div) if body_div else ""

    # Clean: remove script/style tags, then extract text
    body_soup = BeautifulSoup(body_html, "html.parser")
    # Remove images
    for img in body_soup.find_all("img"):
        img.decompose()
    for script in body_soup.find_all("script"):
        script.decompose()

    # Extract paragraphs
    paragraphs = body_soup.find_all("p")
    lines = []
    for p in paragraphs:
        text = p.get_text(strip=True)
        # Skip empty or purely navigation lines
        if not text or len(text) < 2:
            continue
        # Skip junk
        if text in ["语音播报", "缩小字体", "放大字体", "微博", "微信", "分享", "0"]:
            continue
        # Check if it's a header-like line (starts with 一、二、三 etc or contains 聊)
        if re.match(r'^[一二三四五六七八九十]、', text):
            lines.append(f"\n## {text}\n")
        elif text.startswith("方三文：") or text.startswith("段永平："):
            # Q&A format
            lines.append(f"\n**{text.split('：')[0]}：**{text.split('：', 1)[1]}")
        elif re.match(r'^\d+\.', text):
            lines.append(f"\n{text}")
        else:
            lines.append(f"\n{text}")

    body = "\n".join(lines)

    markdown = f"""---
title: "{title_text}"
source: "新浪财经（{source_text}）"
source_url: "{source_url}"
date: {date_str}
type: article
---

# {title_text}

{body}
"""
    output_path = os.path.join(OUTPUT_DIR, "2025-方三文对话段永平.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"  -> {output_path} ({len(markdown)} chars)")


# ─── File 2: sohu_stanford_2018.html ───
def convert_file2():
    print("Converting file 2: sohu_stanford_2018.html")
    path = os.path.join(INPUT_DIR, "sohu_stanford_2018.html")
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Title from h1
    title_tag = soup.find("h1")
    title_text = title_tag.get_text(strip=True) if title_tag else "在斯坦福对话段永平：Stop Doing List"
    # Clean the title
    title_text = re.sub(r'\s+', ' ', title_text).strip()

    # Date from span.time
    time_span = soup.find("span", class_="time")
    date_raw = time_span.get_text(strip=True) if time_span else "2018-10-03"
    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_raw)
    date_str = date_match.group(0) if date_match else "2018-10-03"

    source_text = "搜狐/格隆汇"
    source_url = "https://www.sohu.com/a/257513593_313170"

    # Body: article#mp-editor
    article = soup.find("article", id="mp-editor")
    body_html = str(article) if article else ""

    body_soup = BeautifulSoup(body_html, "html.parser")
    # Remove script/style
    for s in body_soup.find_all(["script", "style"]):
        s.decompose()

    # Process paragraphs and list items
    lines = []
    for elem in body_soup.find_all(["p", "li"]):
        tag = elem.name
        text = elem.get_text(strip=True)
        if not text or len(text) < 2:
            continue

        # Clean up excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        if tag == "li":
            lines.append(f"- {text}")
        else:
            # Check for bold markers or Q&A
            strongs = elem.find_all("strong")
            if strongs and len(strongs) == 1:
                full_strong = strongs[0].get_text(strip=True)
                if full_strong == text:
                    # Entire paragraph is bold
                    # Check if it's a section header like "我的学习笔记："
                    if "学习笔记" in text:
                        lines.append(f"\n> {text}")
                    else:
                        lines.append(f"\n**{text}**")
                    continue

            # Q&A format
            if text.startswith("问：") or text.startswith("段："):
                lines.append(f"\n**{text}**")
            elif text.startswith("来源：") or "返回搜狐" in text:
                continue  # skip source attribution and nav links
            else:
                lines.append(f"\n{text}")

    body = "\n".join(lines)

    markdown = f"""---
title: "{title_text}"
source: "{source_text}"
source_url: "{source_url}"
date: {date_str}
type: article
---

# {title_text}

{body}
"""
    output_path = os.path.join(OUTPUT_DIR, "2018-斯坦福Stop-Doing-List.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"  -> {output_path} ({len(markdown)} chars)")


# ─── File 3: people_rmwz_2010.html ───
def convert_file3():
    print("Converting file 3: people_rmwz_2010.html")
    path = os.path.join(INPUT_DIR, "people_rmwz_2010.html")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")

    # Title from h1
    h1 = soup.find("h1")
    title_text = h1.get_text(strip=True) if h1 else "段永平的美国投资经"

    # Author from div.lai
    lai_div = soup.find("div", class_="lai")
    author = "唐夏"
    if lai_div:
        lai_text = lai_div.get_text(strip=True)
        author_match = re.match(r'(\S+)', lai_text)
        if author_match:
            author = author_match.group(1)

    date_str = "2010-03-01"
    source_text = "人民文摘"
    source_url = "https://paper.people.com.cn/rmwz/html/2010-03/01/content_527465.htm"

    # Body: use div#ozoom (visible content with proper <p> tags)
    # div#articleContent has nested <P><p>... causing parsing issues
    article_div = soup.find("div", id="ozoom")
    if not article_div:
        article_div = soup.find("div", id="articleContent")

    body_html = str(article_div) if article_div else ""

    # Remove the <!--enpcontent--> comments and fix nested P tags
    body_html = body_html.replace("<!--enpcontent-->", "").replace("<P>", "").replace("</P>", "")

    body_soup = BeautifulSoup(body_html, "html.parser")
    for s in body_soup.find_all(["script", "style"]):
        s.decompose()

    paragraphs = body_soup.find_all("p")
    lines = []
    for i, p in enumerate(paragraphs):
        # Skip wrapper paragraphs that contain nested <p> tags (the outer <P> wrapper)
        if p.find("p"):
            continue

        text = p.get_text(strip=True).replace('\xa0', '').replace('\u3000', '')
        text = text.strip()

        if not text or len(text) < 2:
            continue

        # Check if this is a section header (no punctuation, shorter)
        if i > 0 and len(text) < 20 and not re.search(r'[，。；：""！？、]', text):
            lines.append(f"\n## {text}\n")
        else:
            lines.append(f"\n{text}")

    body = "\n".join(lines)

    markdown = f"""---
title: "{title_text}"
source: "{source_text}"
source_url: "{source_url}"
date: {date_str}
author: "{author}"
type: article
---

# {title_text}

{body}
"""
    output_path = os.path.join(OUTPUT_DIR, "2010-段永平的美国投资经.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"  -> {output_path} ({len(markdown)} chars)")


# ─── File 4: jiemian_bloomberg_cn.html ───
def convert_file4():
    print("Converting file 4: jiemian_bloomberg_cn.html")
    path = os.path.join(INPUT_DIR, "jiemian_bloomberg_cn.html")
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Title from h1 or meta
    title_tag = soup.find("h1", class_="article-title")
    title_text = title_tag.get_text(strip=True) if title_tag else "OPPO、vivo幕后老板段永平：如何在中国击败苹果"

    # Date from data attribute
    info_div = soup.find("div", class_="info")
    date_str = "2017-03-20"
    if info_div:
        timestamp = info_div.get("data-article-publish-time", "")
        if timestamp:
            from datetime import datetime
            dt = datetime.fromtimestamp(int(timestamp))
            date_str = dt.strftime("%Y-%m-%d")

    source_text = "界面新闻（彭博社/Bloomberg）"
    source_url = "https://m.jiemian.com/article/1184950.html"

    # Abstract
    abstract_div = soup.find("div", class_="summery")
    abstract = abstract_div.get_text(strip=True) if abstract_div else ""

    # Body: div.article-content
    content_div = soup.find("div", class_="article-content")
    body_html = str(content_div) if content_div else ""

    body_soup = BeautifulSoup(body_html, "html.parser")
    # Remove ads, scripts
    for s in body_soup.find_all(["script", "style", "div"]):
        if s.name == "div" and "j_ads" in s.get("class", []):
            s.decompose()
        elif s.name in ["script", "style"]:
            s.decompose()

    paragraphs = body_soup.find_all("p")
    lines = []

    if abstract:
        lines.append(f"> {abstract}\n")

    for p in paragraphs:
        text = p.get_text(strip=True)
        if not text or len(text) < 5:
            continue
        # Clean HTML entities
        text = html.unescape(text)
        lines.append(f"\n{text}")

    body = "\n".join(lines)

    markdown = f"""---
title: "{title_text}"
source: "{source_text}"
source_url: "{source_url}"
date: {date_str}
type: article
---

# {title_text}

{body}
"""
    output_path = os.path.join(OUTPUT_DIR, "2017-Bloomberg-OPPO-vivo幕后.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"  -> {output_path} ({len(markdown)} chars)")


# ─── Run all ───
if __name__ == "__main__":
    try:
        convert_file1()
    except Exception as e:
        print(f"  ERROR file1: {e}")

    try:
        convert_file2()
    except Exception as e:
        print(f"  ERROR file2: {e}")

    try:
        convert_file3()
    except Exception as e:
        print(f"  ERROR file3: {e}")

    try:
        convert_file4()
    except Exception as e:
        print(f"  ERROR file4: {e}")

    print("\nDone! Listing output:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        fpath = os.path.join(OUTPUT_DIR, f)
        size = os.path.getsize(fpath)
        print(f"  {f} ({size:,} bytes)")
