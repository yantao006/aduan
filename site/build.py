#!/usr/bin/env python3
"""Build the timeline-driven Duan Yongping static site."""

from __future__ import annotations

import html
import hashlib
import json
import os
import re
import shutil
from datetime import date
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
KB_DIR = ROOT / "duanyongping-kb"
ANALYSIS_DIR = KB_DIR / "00-analysis"
SITE_DIR = ROOT / "site"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_md(path: Path) -> tuple[dict[str, Any], str]:
    text = read_text(path)
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not match:
        return {}, text
    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        frontmatter = {}
    return frontmatter, text[match.end() :]


def slugify(title: str) -> str:
    title = title.strip()
    person_aliases = {
        "巴菲特": "buffett",
        "芒格": "munger",
        "黄峥": "huangzheng",
        "丁磊": "dinglei",
        "陈明永": "chenmingyong",
        "沈炜": "shenwei",
        "金志江": "jinzhijiang",
        "方三文": "fangsanwen",
        "格雷厄姆": "graham",
        "王石": "wangshi",
    }
    for key, value in person_aliases.items():
        if key in title:
            return value
    title = title.replace("/", "-")
    slug = title.lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    mapping = {
        "stop-doing-list-不为清单": "stop-doing-list",
        "stop-doing-list": "stop-doing-list",
        "stop-doing-list-不为清单": "stop-doing-list",
        "right-business-right-people-right-price": "right-business",
        "做对的事情-把事情做对": "do-right",
        "做对的事情-把事情做对": "do-right",
        "步步高-bbk": "bbk",
        "步步高-(bbk)": "bbk",
        "苹果-apple": "apple",
        "茅台-moutai": "moutai",
        "拼多多-pdd": "pdd",
        "网易-netease": "netease",
        "腾讯-tencent": "tencent",
        "通用电气-ge": "ge",
        "ge-通用电气": "ge",
        "富国银行-wells-fargo": "wells-fargo",
        "沃伦-巴菲特---warren-buffett": "buffett",
        "查理-芒格---charlie-munger": "munger",
        "黄峥---colin-huang": "huangzheng",
        "丁磊---william-ding": "dinglei",
        "陈明永---tony-chen": "chenmingyong",
        "沈炜---shen-wei": "shenwei",
        "本杰明-格雷厄姆---benjamin-graham": "graham",
        "王石": "wangshi",
        "方三文": "fangsanwen",
        "金志江": "jinzhijiang",
        "oppo": "oppo",
        "vivo": "vivo",
    }
    return mapping.get(slug, slug)


def clean_title(title: str) -> str:
    return re.sub(r"\s*/\s*.*$", "", title).replace(" (不为清单)", "").strip()


def load_yaml(name: str) -> Any:
    return yaml.safe_load(read_text(ANALYSIS_DIR / name))


def load_json(name: str) -> Any:
    return json.loads(read_text(ANALYSIS_DIR / name))


def md_inline(text: str) -> str:
    placeholders: list[str] = []

    def keep(value: str) -> str:
        placeholders.append(value)
        return f"@@HTML{len(placeholders) - 1}@@"

    def link_repl(match: re.Match[str]) -> str:
        label = match.group(1).strip() or "原文"
        url = match.group(2).strip()
        if label.lower().startswith("http") or len(label) > 12:
            label = "原文"
        return keep(
            f'<a class="external-source-link" href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">{html.escape(label)}</a>'
        )

    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", link_repl, text)
    text = re.sub(
        r"(?<![\"'=])(https?://[^\s)）]+)",
        lambda m: keep(
            f'<a class="external-source-link" href="{html.escape(m.group(1), quote=True)}" target="_blank" rel="noopener">原文</a>'
        ),
        text,
    )
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", lambda m: m.group(2) or m.group(1), text)
    for i, value in enumerate(placeholders):
        text = text.replace(f"@@HTML{i}@@", value)
    return text


def md_to_html(markdown: str) -> str:
    out: list[str] = []
    in_ul = False
    in_ol = False
    in_quote: list[str] = []
    in_table = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def close_quote() -> None:
        nonlocal in_quote
        if in_quote:
            out.append("<blockquote>" + "<br>".join(md_inline(x) for x in in_quote) + "</blockquote>")
            in_quote = []

    for raw in markdown.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            close_quote()
            close_lists()
            if re.match(r"^\|[\s\-:|]+\|$", stripped):
                continue
            cells = [md_inline(c.strip()) for c in stripped.strip("|").split("|")]
            if not in_table:
                out.append('<div class="table-wrap"><table>')
                in_table = True
                tag = "th"
            else:
                tag = "td"
            out.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</table></div>")
            in_table = False

        if stripped.startswith(">"):
            close_lists()
            in_quote.append(re.sub(r"^>\s?", "", stripped))
            continue
        close_quote()

        if not stripped:
            close_lists()
            continue
        if re.fullmatch(r"-{3,}", stripped):
            close_lists()
            continue
        if stripped.startswith("# "):
            close_lists()
            continue
        if stripped.startswith("## "):
            close_lists()
            out.append(f"<h2>{md_inline(stripped[3:])}</h2>")
            continue
        if stripped.startswith("### "):
            close_lists()
            out.append(f"<h3>{md_inline(stripped[4:])}</h3>")
            continue
        if stripped.startswith("#### "):
            close_lists()
            out.append(f"<h4>{md_inline(stripped[5:])}</h4>")
            continue
        m = re.match(r"^\d+\.\s+(.+)$", stripped)
        if m:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{md_inline(m.group(1))}</li>")
            continue
        m = re.match(r"^[-*]\s+(.+)$", stripped)
        if m:
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{md_inline(m.group(1))}</li>")
            continue
        close_lists()
        out.append(f"<p>{md_inline(stripped)}</p>")

    close_quote()
    close_lists()
    if in_table:
        out.append("</table></div>")
    return "\n".join(out)


def section(body: str, heading: str) -> str:
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            start = i + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return "\n".join(lines[start:end]).strip()


def remove_section(body: str, heading: str) -> str:
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            start = i
            break
    if start is None:
        return body
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return "\n".join(lines[:start] + lines[end:]).strip()


def source_candidates_from_body(body: str) -> list[str]:
    source_text = section(body, "原话出处") or section(body, "关键出处")
    candidates: list[str] = []
    for match in re.finditer(r"`([^`]+)`", source_text):
        candidates.append(match.group(1))
    for line in source_text.splitlines():
        line = line.strip("-* \t")
        if "/" in line and ".md" in line:
            candidates.append(line.split("：")[-1].strip())
    deduped = []
    for item in candidates:
        item = item.strip()
        if item and item not in deduped:
            deduped.append(item)
    return deduped


def strip_source_sections(body: str) -> str:
    for heading in ["跨引用", "原话出处", "关键出处"]:
        body = remove_section(body, heading)
    return body


def split_markdown_sections(body: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_title = ""
    current_lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current_title or current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_title or current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))
    return [(title, content) for title, content in sections if title or content]


def is_timeline_heading(title: str) -> bool:
    return bool(re.search(r"(?:19|20)\d{2}[-年]\d{1,2}|(?:19|20)\d{2}-\d{1,2}-\d{1,2}", title))


def source_body_html(info: dict[str, Any], body: str) -> str:
    body = strip_source_sections(body)
    sections = split_markdown_sections(body)
    if not sections:
        return f"<section class='paper-panel article-body source-section'>{md_to_html(body)}</section>" if body.strip() else ""

    timeline_like = "雪球时间线" in info.get("title", "") or sum(1 for title, _ in sections if is_timeline_heading(title)) >= 2
    if timeline_like:
        entries = []
        intro = []
        for title, content in sections:
            if not title:
                if content:
                    rendered = md_to_html(content)
                    if rendered.strip():
                        intro.append(rendered)
                continue
            if is_timeline_heading(title):
                entries.append(
                    f"""<article class="source-entry">
                      <header>{md_inline(title)}</header>
                      <div class="article-body">{md_to_html(content)}</div>
                    </article>"""
                )
            else:
                intro.append(f"<section class='source-section'><h2>{md_inline(title)}</h2>{md_to_html(content)}</section>")
        intro_html = f"<section class='paper-panel article-body source-section'>{''.join(intro)}</section>" if intro else ""
        return intro_html + f"<section class='source-entry-list'>{''.join(entries)}</section>"

    cards = []
    for title, content in sections:
        if not title and not content:
            continue
        heading = f"<h2>{md_inline(title)}</h2>" if title else ""
        rendered = md_to_html(content)
        if not heading and not rendered.strip():
            continue
        cards.append(f"<section class='paper-panel article-body source-section'>{heading}{rendered}</section>")
    return "".join(cards)


def first_blockquote(body: str) -> str:
    quote_lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            quote_lines.append(re.sub(r"^>\s?", "", stripped))
        elif quote_lines:
            break
    return "\n".join(quote_lines).strip()


def brief_section(body: str, heading: str, max_chars: int = 110) -> str:
    text = section(body, heading)
    text = re.sub(r"^#+\s+.*$", "", text, flags=re.M)
    text = re.sub(r">.*", "", text)
    text = re.sub(r"\|.*\|", "", text)
    text = re.sub(r"[-*]\s+", "", text)
    text = re.sub(r"\d+\.\s+", "", text)
    text = re.sub(r"\s+", " ", text).strip(" -")
    if len(text) > max_chars:
        return text[:max_chars].rstrip("，。；： ") + "。"
    return text


def quote_attributions(body: str) -> list[str]:
    sources = []
    for line in body.splitlines():
        stripped = line.strip("> \t")
        if stripped.startswith("——"):
            value = stripped.lstrip("——").strip()
            if not re.search(r"(?:19|20)\d{2}|斯坦福|浙大|北大|人大|波士堂|访谈|对话|演讲|交流|讲话|博客|雪球|销售手册|企业文化", value):
                continue
            if value and value not in sources:
                sources.append(value)
    return sources


def sdl_summary(item: dict[str, Any]) -> str:
    if item.get("relationship"):
        return item["relationship"]
    body = item.get("body", "")
    return (
        brief_section(body, "为什么「不做空」是第一戒律？")
        or brief_section(body, "为什么「不借钱」是铁律？")
        or brief_section(body, "核心要义")
        or brief_section(body, "为什么")
        or item.get("severity", "")
    )


def source_display_label(source: str) -> str:
    path = resolve_source_path(source) if is_packable_source(source) else None
    path_exists = bool(path and path.exists())
    title = html.escape(infer_source_title(source, path if path_exists else None))
    date_text = html.escape(infer_source_date(source, path if path_exists else None))
    return f"{date_text} · 《{title}》" if date_text else f"《{title}》"


def source_has_content(info: dict[str, Any]) -> bool:
    path = info.get("path")
    return bool((path and Path(path).exists()) or info.get("excerpts"))


def sdl_source_block(item: dict[str, Any]) -> str:
    candidates = source_candidates_from_body(item["body"]) + quote_attributions(item["body"])
    links: list[str] = []
    notes: list[str] = []
    for source in dict.fromkeys(candidates):
        if not is_packable_source(source):
            notes.append(html.escape(clean_source_title(source)))
            continue
        info = register_source(source)
        if source_has_content(info):
            links.append(cite_html(source))
        else:
            notes.append(source_display_label(source))
    links_html = "".join(f"<li>{link}</li>" for link in dict.fromkeys(x for x in links if x))
    notes_html = "".join(f"<li>{note}</li>" for note in dict.fromkeys(x for x in notes if x))
    if not links_html and not notes_html:
        return ""
    readable = f"<div><h3>可阅读来源</h3><ul>{links_html}</ul></div>" if links_html else ""
    attributions = f"<div><h3>出处说明</h3><ul>{notes_html}</ul></div>" if notes_html else ""
    return f"<section class='paper-panel source-list split-source-list'><h2>来源</h2>{readable}{attributions}</section>"


def load_items() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    def load_folder(folder: str, kind: str) -> list[dict[str, Any]]:
        items = []
        for path in sorted((KB_DIR / folder).glob("*.md")):
            if path.name == "README.md":
                continue
            fm, body = parse_md(path)
            if not fm:
                continue
            title = fm.get("title", path.stem)
            items.append(
                {
                    "title": title,
                    "short_title": clean_title(title),
                    "slug": slugify(title),
                    "kind": kind,
                    "category": fm.get("category", ""),
                    "mentioned_count": fm.get("mentioned_count", 0) or 0,
                    "first_seen": str(fm.get("first_seen", "") or ""),
                    "last_seen": str(fm.get("last_seen", "") or ""),
                    "related_concepts": fm.get("related_concepts", []) or [],
                    "related_companies": fm.get("related_companies", []) or [],
                    "related_people": fm.get("related_people", []) or [],
                    "relationship": fm.get("relationship", "") or "",
                    "severity": fm.get("severity", "") or "",
                    "sdl_number": fm.get("sdl_number", "") or "",
                    "path": str(path.relative_to(ROOT)),
                    "body": body,
                }
            )
        return items

    return (
        load_folder("01-投资概念", "concept"),
        load_folder("03-企业与品牌", "company"),
        load_folder("04-关键人物", "person"),
        load_folder("02-Stop-Doing-List", "sdl"),
    )


concepts, companies, people, sdl_items = load_items()
items_by_title = {item["title"]: item for group in [concepts, companies, people, sdl_items] for item in group}
items_by_short = {item["short_title"]: item for group in [concepts, companies, people, sdl_items] for item in group}
source_registry: dict[str, dict[str, Any]] = {}
alias_lookup = {
    "巴菲特": "沃伦·巴菲特 / Warren Buffett",
    "老巴": "沃伦·巴菲特 / Warren Buffett",
    "芒格": "查理·芒格 / Charlie Munger",
    "黄峥": "黄峥 / Colin Huang",
    "丁磊": "丁磊 / William Ding",
    "陈明永": "陈明永 / Tony Chen",
    "沈炜": "沈炜 / Shen Wei",
    "格雷厄姆": "本杰明·格雷厄姆 / Benjamin Graham",
    "苹果": "苹果/Apple",
    "茅台": "茅台/Moutai",
    "网易": "网易/NetEase",
    "拼多多": "拼多多/PDD",
    "腾讯": "腾讯/Tencent",
    "GE": "通用电气/GE",
    "通用电气": "通用电气/GE",
    "富国银行": "富国银行/Wells Fargo",
    "OPPO": "OPPO",
    "vivo": "vivo",
    "步步高": "步步高 (BBK)",
}

external_links = {
    "段永平": [("维基百科", "https://zh.wikipedia.org/wiki/%E6%AE%B5%E6%B0%B8%E5%B9%B3")],
    "沃伦·巴菲特": [("Wikipedia", "https://en.wikipedia.org/wiki/Warren_Buffett")],
    "巴菲特": [("Wikipedia", "https://en.wikipedia.org/wiki/Warren_Buffett")],
    "查理·芒格": [("Wikipedia", "https://en.wikipedia.org/wiki/Charlie_Munger")],
    "芒格": [("Wikipedia", "https://en.wikipedia.org/wiki/Charlie_Munger")],
    "黄峥": [("Wikipedia", "https://en.wikipedia.org/wiki/Colin_Huang")],
    "丁磊": [("Wikipedia", "https://en.wikipedia.org/wiki/Ding_Lei")],
    "陈明永": [("OPPO", "https://www.oppo.com/")],
    "沈炜": [("vivo", "https://www.vivo.com/")],
    "方三文": [("雪球", "https://xueqiu.com/")],
    "本杰明·格雷厄姆": [("Wikipedia", "https://en.wikipedia.org/wiki/Benjamin_Graham")],
    "格雷厄姆": [("Wikipedia", "https://en.wikipedia.org/wiki/Benjamin_Graham")],
    "王石": [("Wikipedia", "https://en.wikipedia.org/wiki/Wang_Shi")],
    "苹果": [("官网", "https://www.apple.com/"), ("投资者关系", "https://investor.apple.com/")],
    "Apple": [("官网", "https://www.apple.com/"), ("投资者关系", "https://investor.apple.com/")],
    "茅台": [("官网", "https://www.moutaichina.com/")],
    "Moutai": [("官网", "https://www.moutaichina.com/")],
    "网易": [("官网", "https://www.163.com/"), ("投资者关系", "https://ir.netease.com/")],
    "NetEase": [("官网", "https://www.163.com/"), ("投资者关系", "https://ir.netease.com/")],
    "拼多多": [("官网", "https://www.pinduoduo.com/"), ("投资者关系", "https://investor.pddholdings.com/")],
    "PDD": [("官网", "https://www.pinduoduo.com/"), ("投资者关系", "https://investor.pddholdings.com/")],
    "腾讯": [("官网", "https://www.tencent.com/"), ("投资者关系", "https://www.tencent.com/en-us/investors.html")],
    "Tencent": [("官网", "https://www.tencent.com/"), ("投资者关系", "https://www.tencent.com/en-us/investors.html")],
    "OPPO": [("官网", "https://www.oppo.com/")],
    "vivo": [("官网", "https://www.vivo.com/")],
    "步步高": [("官网", "https://www.gdbbk.com/")],
    "BBK": [("官网", "https://www.gdbbk.com/")],
    "通用电气": [("官网", "https://www.ge.com/"), ("投资者关系", "https://www.ge.com/investor-relations")],
    "GE": [("官网", "https://www.ge.com/"), ("投资者关系", "https://www.ge.com/investor-relations")],
    "富国银行": [("官网", "https://www.wellsfargo.com/"), ("投资者关系", "https://www.wellsfargo.com/about/investor-relations/")],
    "Wells Fargo": [("官网", "https://www.wellsfargo.com/"), ("投资者关系", "https://www.wellsfargo.com/about/investor-relations/")],
}
events_data = load_yaml("events.yaml")
concept_evolution = load_yaml("concept-evolution.yaml")["concepts"]
quote_data = load_yaml("quote-selections.yaml")
company_cases = load_yaml("company-case-timeline.yaml")["companies"]
concept_frequency = load_json("concept-frequency.json")
timeline_index = load_json("timeline-index.json")


def url_for_title(title: str, kind_hint: str | None = None) -> str | None:
    resolved = alias_lookup.get(title, title)
    item = items_by_title.get(resolved) or items_by_short.get(clean_title(resolved))
    if not item:
        return None
    folder = {"concept": "concept", "company": "company", "person": "person", "sdl": "stop-doing"}.get(item["kind"])
    if item["kind"] == "sdl":
        return f"/stop-doing/{item['slug']}.html"
    return f"/{folder}/{item['slug']}.html"


def infer_source_date(source: str, path: Path | None = None) -> str:
    text = str(path or source)
    match = re.search(r"((?:19|20)\d{2})(?:[-年_](\d{1,2}))?", text)
    if not match:
        return ""
    if match.group(2):
        return f"{match.group(1)}-{int(match.group(2)):02d}"
    return match.group(1)


def infer_source_title(source: str, path: Path | None = None) -> str:
    if path and path.exists() and path.suffix == ".md":
        fm, body = parse_md(path)
        if fm.get("title"):
            return clean_source_title(str(fm["title"]))
        first_heading = re.search(r"^#\s+(.+)$", body, re.M)
        if first_heading:
            return clean_source_title(first_heading.group(1))
    raw = path.stem if path else source
    return clean_source_title(raw)


def clean_source_title(title: str) -> str:
    title = re.sub(r"\.md$", "", title.strip())
    title = title.replace(".md-", "-").replace(".md", "")
    title = re.sub(r"^\d+-", "", title)
    title = re.sub(r"^(?:19|20)\d{2}[-年_ ]*", "", title)
    title = re.sub(r"（推测）", "", title)
    title = title.replace("_@大道无形我有型", " 雪球时间线")
    title = title.replace("@大道无形我有型", "雪球时间线")
    title = title.replace("段永平雪球问答录_杨不为整理-仅保留首轮对话版-", "雪球问答录 ")
    return title.strip(" -_")


def source_slug(title: str, source: str) -> str:
    base = slugify(title)
    if not base or len(base) < 2:
        base = "source"
    suffix = hashlib.sha1(source.encode("utf-8")).hexdigest()[:8]
    return f"{base}-{suffix}"


def register_source(source: str, quote: str | None = None) -> dict[str, Any]:
    source = str(source or "").strip()
    if not source:
        source = "未标明出处"
    if source in source_registry:
        if quote:
            source_registry[source].setdefault("excerpts", [])
            if quote not in source_registry[source]["excerpts"]:
                source_registry[source]["excerpts"].append(quote)
        return source_registry[source]
    path = resolve_source_path(source)
    path_exists = path.exists()
    title = infer_source_title(source, path if path_exists else None)
    date = infer_source_date(source, path if path_exists else None)
    slug = source_slug(title, source)
    info = {
        "source": source,
        "path": path if path_exists else None,
        "title": title or "未命名资料",
        "date": date,
        "url": f"/sources/{slug}.html",
        "excerpts": [quote] if quote else [],
    }
    source_registry[source] = info
    return info


def resolve_source_path(source: str) -> Path:
    candidates = [
        ROOT / source,
        KB_DIR / source,
        ROOT / "duanyongping" / source,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return ROOT / source


def is_packable_source(source: str) -> bool:
    source = str(source or "").strip()
    if not source:
        return False
    if any(token in source.lower() for token in ["execution-plan", "readme.md", "00-analysis"]):
        return False
    if "/" in source or source.endswith(".md"):
        return resolve_source_path(source).exists()
    return True


def source_type(info: dict[str, Any]) -> str:
    title = f"{info.get('title','')} {info.get('source','')}"
    if any(k in title for k in ["雪球", "问答"]):
        return "雪球问答"
    if any(k in title for k in ["斯坦福", "北大", "浙大", "演讲", "交流"]):
        return "演讲交流"
    if any(k in title for k in ["访谈", "对话", "波士堂"]):
        return "访谈对话"
    if any(k in title for k in ["讲话", "企业文化", "销售手册"]):
        return "企业资料"
    return "资料"


def cite_html(source: str, quote: str | None = None, date_override: str | None = None) -> str:
    if not is_packable_source(source):
        return ""
    info = register_source(source, quote)
    if not source_has_content(info):
        return ""
    title = html.escape(info["title"])
    date_text = html.escape(date_override or info["date"])
    label = f"{date_text} · 《{title}》" if date_text else f"《{title}》"
    return f'<a class="source-link" href="{info["url"]}">{label}</a>'


def tag_links(names: list[str], fallback_kind: str = "concept") -> str:
    tags = []
    for name in names:
        url = url_for_title(name, fallback_kind)
        label = html.escape(clean_title(name))
        if url:
            tags.append(f'<a class="tag" href="{url}">{label}</a>')
        else:
            tags.append(f'<span class="tag">{label}</span>')
    return "".join(tags)


def external_links_html(title: str) -> str:
    candidates = [title, clean_title(title)]
    candidates += [part.strip() for part in re.split(r"[/()（）]", title) if part.strip()]
    links: list[tuple[str, str]] = []
    for candidate in candidates:
        for item in external_links.get(candidate, []):
            if item not in links:
                links.append(item)
    if not links:
        return ""
    anchors = "".join(
        f'<a class="external-source-link" href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">{html.escape(label)}</a>'
        for label, url in links
    )
    return f'<div class="external-links"><span>外部资料</span>{anchors}</div>'


def search_box() -> str:
    return """
<div class="search-shell">
  <label class="search-label" for="global-search">搜索</label>
  <input id="global-search" type="search" placeholder="搜索知识库..." autocomplete="off">
  <kbd>⌘ K</kbd>
  <div id="search-results" class="search-results"></div>
</div>
"""


def page(title: str, body: str, active: str = "") -> str:
    nav = [
        ("/", "首页", "home"),
        ("/timeline.html", "思想年表", "timeline"),
        ("/concepts.html", "核心概念", "concepts"),
        ("/companies.html", "企业档案", "companies"),
        ("/people.html", "人物关系", "people"),
        ("/stop-doing.html", "不为清单", "sdl"),
        ("/graph.html", "知识图谱", "graph"),
    ]
    nav_html = "".join(
        f'<a class="nav-link {"active" if key == active else ""}" href="{href}">{label}</a>'
        for href, label, key in nav
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} · 段永平投资知识库</title>
  <link rel="stylesheet" href="/style.css">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="/">
      <span class="brand-mark">段</span>
      <span><strong>段永平投资知识库</strong><small>理解本质，做时间的朋友</small></span>
    </a>
    <nav class="top-nav">{nav_html}</nav>
    {search_box()}
  </header>
  <main>{body}</main>
  <footer class="site-footer">
    <span>基于公开演讲、博客、访谈、雪球问答整理。频次统计仅作线索，不构成投资建议。</span>
  </footer>
  <script src="/search.js"></script>
</body>
</html>"""


def write_page(path: str, title: str, content: str, active: str = "") -> None:
    out = SITE_DIR / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page(title, content, active), encoding="utf-8")
    print(f"wrote {path}")


def sparkline_svg(series: dict[str, int], width: int = 680, height: int = 220) -> str:
    years = list(range(2010, 2027))
    values = [int(series.get(str(y), 0)) for y in years]
    max_v = max(values) if values else 0
    left, right, top, bottom = 44, 18, 18, 38
    plot_w = width - left - right
    plot_h = height - top - bottom
    if max_v == 0:
        max_v = 1
    pts = []
    for i, value in enumerate(values):
        x = left + (plot_w * i / max(1, len(years) - 1))
        y = top + plot_h - (value / max_v * plot_h)
        pts.append((x, y, value, years[i]))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in pts)
    grid = "".join(
        f'<line x1="{left}" y1="{top + plot_h * i / 4:.1f}" x2="{width-right}" y2="{top + plot_h * i / 4:.1f}" />'
        for i in range(5)
    )
    circles = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4"><title>{year}: {value}</title></circle>'
        for x, y, value, year in pts
        if value
    )
    labels = "".join(
        f'<text x="{x:.1f}" y="{height-12}" text-anchor="middle">{year}</text>'
        for x, _, _, year in pts
        if year in {2010, 2013, 2016, 2019, 2022, 2025}
    )
    peak = max(pts, key=lambda p: p[2])
    label_y = max(6, peak[1] - 38)
    peak_label = (
        f'<g class="chart-peak"><rect x="{peak[0]-26:.1f}" y="{label_y:.1f}" width="52" height="28" rx="4"/>'
        f'<text x="{peak[0]:.1f}" y="{label_y+18:.1f}" text-anchor="middle">{peak[3]}</text>'
        f'<text x="{peak[0]:.1f}" y="{label_y+30:.1f}" text-anchor="middle">{peak[2]}次</text></g>'
        if peak[2]
        else ""
    )
    return f"""<svg class="freq-chart" viewBox="0 0 {width} {height}" role="img">
  <g class="chart-grid">{grid}</g>
  <polyline points="{poly}" />
  <g class="chart-points">{circles}</g>
  {peak_label}
  <g class="chart-labels">{labels}</g>
</svg>"""


def concept_card_kicker(title: str) -> str:
    return {
        "买股票就是买公司": "投资入口",
        "未来现金流折现": "估值底层",
        "能力圈": "边界意识",
        "护城河": "长期优势",
        "本分": "经营底色",
        "平常心": "理性状态",
        "Stop Doing List (不为清单)": "少犯大错",
        "商业模式": "现金流来源",
    }.get(title, "概念")


def concept_card_line(title: str) -> str:
    return {
        "买股票就是买公司": "一句话打开整个投资框架。",
        "未来现金流折现": "价格之外，先问公司能创造什么。",
        "能力圈": "知道不懂什么，比知道什么更重要。",
        "护城河": "好公司经得起时间和竞争反复验证。",
        "本分": "不被短期利益带偏的经营原则。",
        "平常心": "把情绪拿掉，回到事情本身。",
        "Stop Doing List (不为清单)": "不做错事，才有机会长期做对事。",
        "商业模式": "生意如何赚钱，决定现金流质量。",
    }.get(title, "查看这个概念如何随时间变化。")


def company_card_kicker(title: str) -> str:
    return {
        "茅台/Moutai": "价格纪律",
        "苹果/Apple": "好生意样本",
        "网易/NetEase": "早期验证",
        "拼多多/PDD": "新案例",
        "通用电气/GE": "纠错样本",
        "腾讯/Tencent": "机会成本",
        "步步高 (BBK)": "文化源头",
        "OPPO": "不做代工",
        "vivo": "本分外化",
        "富国银行/Wells Fargo": "风险警示",
    }.get(title, "企业案例")


def company_card_line(title: str) -> str:
    return {
        "茅台/Moutai": "确定性、品牌和好价格的一次长期检验。",
        "苹果/Apple": "关于生态、护城河和长期持有的核心样本。",
        "网易/NetEase": "从低估到重仓，“买公司”的早期验证。",
        "拼多多/PDD": "商业模式、创始人和不确定性边界。",
        "通用电气/GE": "赚钱但仍可能是错的，一次关于纠错的样本。",
        "腾讯/Tencent": "平台生意与机会成本的观察样本。",
        "步步高 (BBK)": "本分、授权和不为清单的源头。",
        "OPPO": "消费者导向与经营边界的实践。",
        "vivo": "企业文化如何延续到三十年。",
        "富国银行/Wells Fargo": "金融业务与文化变化的风险提醒。",
    }.get(title, "进入案例，查看它验证了什么。")


def person_card_line(title: str, relationship: str = "") -> str:
    return {
        "沃伦·巴菲特 / Warren Buffett": "把投资重新拉回公司所有权。",
        "查理·芒格 / Charlie Munger": "理性、能力圈和少犯错的思想来源。",
        "黄峥 / Colin Huang": "新一代创业者与拼多多案例的连接点。",
        "丁磊 / William Ding": "网易案例背后的企业家参照。",
        "陈明永 / Tony Chen": "OPPO 路线和长期授权的实践者。",
        "沈炜 / Shen Wei": "本分文化的系统阐释者。",
        "金志江": "步步高体系中的经营伙伴。",
        "方三文": "把零散问答整理成系统对话的人。",
        "本杰明·格雷厄姆 / Benjamin Graham": "价值投资源头，影响巴菲特也影响段永平。",
        "王石": "企业家视角下的长期主义对话对象。",
    }.get(title, relationship or "查看他和段永平思想网络中的位置。")


def home_page() -> str:
    events = events_data["events"]
    today_pool = quote_data.get("today_pool", [])
    today_index = int(hashlib.sha1(date.today().isoformat().encode("utf-8")).hexdigest(), 16) % max(1, len(today_pool))
    today = today_pool[today_index] if today_pool else {}
    top_concepts = [c for c in concepts if concept_evolution.get(c["title"], {}).get("core_for_timeline")]
    concept_cards = "".join(
        f"""<a class="concept-tile" href="/concept/{c['slug']}.html">
          <span>{html.escape(concept_card_kicker(c['title']))}</span>
          <strong>{html.escape(clean_title(c['title']))}</strong>
          <small>{html.escape(concept_card_line(c['title']))}</small>
          <em>查看</em>
        </a>"""
        for c in top_concepts
    )
    event_cards = "".join(
        f"""<article class="event-card {'featured' if e['year'] == 2010 else ''}" data-year="{e['year']}">
          <time>{e['year']}</time>
          <h3>{html.escape(e['title'])}</h3>
          <p>{html.escape(e['summary'])}</p>
          <a href="/timeline.html#year-{e['year']}">展开这一年</a>
        </article>"""
        for e in events
    )
    ticks = "".join(
        f'<button class="timeline-dot" data-year="{e["year"]}" style="--x:{(e["year"]-1995)/(2025-1995)*100:.2f}%"><span>{e["year"]}</span></button>'
        for e in events
    )
    companies_html = "".join(
        f"""<a class="mini-card" href="/company/{c['slug']}.html">
          <span>{html.escape(company_card_kicker(c['title']))}</span>
          <strong>{html.escape(clean_title(c['title']))}</strong>
          <small>{html.escape(company_card_line(c['title']))}</small>
          <em>进入案例</em>
        </a>"""
        for c in sorted(companies, key=lambda x: x["mentioned_count"], reverse=True)[:6]
    )
    return f"""
<section class="hero">
  <div>
    <p class="eyebrow">段永平思想年表</p>
    <h1>经营、投资与不为清单。</h1>
    <p class="hero-copy">从步步高、OPPO、vivo，到网易、苹果、茅台、拼多多，按年份整理公开发言中的判断、案例和出处。</p>
  </div>
  <aside class="today-quote">
    <span>今日段永平</span>
    <blockquote>{html.escape(today.get('text', ''))}</blockquote>
    <small>{cite_html(today.get('source', ''), today.get('text', ''), today.get('date', '')) if today else ''}</small>
  </aside>
</section>

<section class="timeline-panel">
  <div class="section-head">
    <div><h2>思想年表</h2><p>关键年份、概念和案例。</p></div>
    <a class="text-link" href="/timeline.html">进入完整年表</a>
  </div>
  <div class="timeline-track" aria-label="关键事件时间轴">
    <div class="track-line"></div>
    {ticks}
  </div>
  <div class="event-strip">{event_cards}</div>
</section>

<section class="split-section">
  <div>
    <div class="section-head"><div><h2>核心概念</h2><p>高频概念与关键出处。</p></div><a class="text-link" href="/concepts.html">查看全部</a></div>
    <div class="concept-grid">{concept_cards}</div>
  </div>
  <aside class="paper-note start-note">
    <h2>从这里开始</h2>
    <div class="quick-links">
      <a href="/concept/买股票就是买公司.html"><span>2010</span><strong>买股票就是买公司</strong></a>
      <a href="/concept/stop-doing-list.html"><span>2018</span><strong>Stop Doing List</strong></a>
      <a href="/company/apple.html"><span>2011</span><strong>苹果案例</strong></a>
    </div>
  </aside>
</section>

<section>
  <div class="section-head"><div><h2>企业案例</h2><p>网易、苹果、茅台、拼多多、GE。</p></div><a class="text-link" href="/companies.html">查看全部</a></div>
  <div class="mini-grid">{companies_html}</div>
</section>
<script src="/timeline.js"></script>
"""


def timeline_page() -> str:
    chapters = events_data["chapters"]
    events = events_data["events"]
    chapters_html = ""
    for chapter in chapters:
        chapter_events = [e for e in events if e["chapter"] == chapter["title"]]
        if not chapter_events:
            continue
        cards = "".join(
            f"""<article class="story-event" id="year-{e['year']}">
              <time>{e['year']}</time>
              <div>
                <h3>{html.escape(e['title'])}</h3>
                <p>{html.escape(e['summary'])}</p>
                <div class="tag-row">{tag_links(e.get('concepts', []))}</div>
              </div>
            </article>"""
            for e in chapter_events
        )
        chapters_html += f"""<section class="story-chapter">
          <div class="chapter-title"><span>{html.escape(chapter['years'])}</span><h2>{html.escape(chapter['title'])}</h2></div>
          <div class="story-events">{cards}</div>
        </section>"""
    year_nav = "".join(f'<a href="#year-{e["year"]}">{e["year"]}</a>' for e in events)
    return f"""
<section class="page-hero compact">
  <p class="eyebrow">思想年表</p>
  <h1>段永平思想年表</h1>
  <p>经营原则、投资框架和企业案例按年份排列。</p>
</section>
<nav class="year-rail">{year_nav}</nav>
<div class="story-layout">
  <aside class="story-aside">
    <h2>阅读线索</h2>
    <p>年份节点连接概念、企业、人物和来源。</p>
  </aside>
  <div>{chapters_html}</div>
</div>
"""


def concepts_page() -> str:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for concept in concepts:
        groups[concept["category"]].append(concept)
    sections = ""
    for category, group in sorted(groups.items()):
        cards = "".join(
            f"""<a class="archive-card" href="/concept/{c['slug']}.html">
              <span>{html.escape('公司 / 案例' if category == '投资案例' else concept_card_kicker(c['title']))}</span>
              <h3>{html.escape(clean_title(c['title']))}</h3>
              <p>{html.escape(concept_card_line(c['title']))}</p>
              <em>{html.escape('进入案例脉络' if category == '投资案例' else c['first_seen'] + ' 起')}</em>
            </a>"""
            for c in sorted(group, key=lambda x: x["mentioned_count"], reverse=True)
        )
        sections += f"<section><h2>{html.escape(category)}</h2><div class='archive-grid'>{cards}</div></section>"
    return f"""
<section class="page-hero compact">
  <p class="eyebrow">核心概念</p>
  <h1>高频概念与关键出处。</h1>
  <p>每个概念保留频次、演变、原话和关联阅读。</p>
</section>
{sections}
"""


def concept_page(concept: dict[str, Any]) -> str:
    evolution = concept_evolution.get(concept["title"], {})
    quotes = quote_data["by_concept"].get(concept["title"], [])
    phases = "".join(
        f"""<li><span>{html.escape(str(p.get('period') or '阶段'))}</span><p>{html.escape(p.get('summary', ''))}</p></li>"""
        for p in evolution.get("phases", [])
    )
    quote_html = "".join(
        f"""<blockquote class="quote-card"><p>{html.escape(q['text'])}</p><cite>{cite_html(q.get('source',''), q.get('text',''), q.get('date',''))}</cite></blockquote>"""
        for q in quotes[:5]
    )
    related = tag_links(concept.get("related_concepts", [])) + tag_links(concept.get("related_companies", []), "company") + tag_links(concept.get("related_people", []), "person")
    core = "核心概念" if evolution.get("core_for_timeline") else concept["category"]
    body_intro = section(concept["body"], "核心要义") or section(concept["body"], "段永平怎么说")
    return f"""
<article class="detail-page">
  <header class="detail-header">
    <p class="eyebrow">{html.escape(core)}</p>
    <h1>{html.escape(clean_title(concept['title']))}</h1>
    <p>{html.escape(concept_card_line(concept['title']))}</p>
    <div class="meta-line">
      <span>{html.escape(concept['category'])}</span>
      <span>{html.escape(concept['first_seen'])} - {html.escape(concept['last_seen'])}</span>
    </div>
  </header>
  <section class="paper-panel">
    <div class="section-head"><div><h2>年度提及频次</h2></div></div>
    {sparkline_svg(concept_frequency.get(concept['title'], {}))}
  </section>
  <section class="detail-grid">
    <div class="paper-panel">
      <h2>概念演变轨迹</h2>
      <ol class="evolution-list">{phases}</ol>
    </div>
    <div class="paper-panel">
      <h2>原话摘录</h2>
      {quote_html}
    </div>
  </section>
  <section class="paper-panel article-body">
    <h2>核心要义</h2>
    {md_to_html(body_intro)}
  </section>
  <section class="related-block"><h2>关联阅读</h2><div class="tag-row">{related}</div></section>
</article>
"""


def companies_page() -> str:
    cards = "".join(
        f"""<a class="archive-card wide" href="/company/{c['slug']}.html">
          <span>{html.escape(company_card_kicker(c['title']))}</span>
          <h3>{html.escape(clean_title(c['title']))}</h3>
          <p>{html.escape(company_card_line(c['title']))}</p>
          <em>进入案例</em>
        </a>"""
        for c in sorted(companies, key=lambda x: x["mentioned_count"], reverse=True)
    )
    return f"""
<section class="page-hero compact">
  <p class="eyebrow">企业档案</p>
  <h1>企业案例</h1>
  <p>网易、苹果、茅台、拼多多、GE。</p>
</section>
<div class="archive-grid two">{cards}</div>
"""


def company_page(company: dict[str, Any]) -> str:
    case = company_cases.get(company["title"], {})
    source_links = []
    for source in [case.get("source_card", "")] + source_candidates_from_body(company["body"]):
        if is_packable_source(source):
            source_links.append(cite_html(source))
    source_links_html = "".join(f"<li>{link}</li>" for link in dict.fromkeys(link for link in source_links if link))
    timeline = "".join(
        f"""<li><span>{html.escape(str(row.get('period','')))}</span><p>{html.escape(row.get('event',''))}</p></li>"""
        for row in case.get("timeline", [])
    )
    quote_candidates = [
        q for q in case.get("representative_quotes", [])
        if "详细投资案例分析" not in q and "参见" not in q
    ][:4]
    quotes = "".join(f"<blockquote class='quote-card'><p>{md_inline(q)}</p></blockquote>" for q in quote_candidates)
    return f"""
<article class="detail-page">
  <header class="detail-header">
    <p class="eyebrow">{html.escape(company['category'])}</p>
    <h1>{html.escape(clean_title(company['title']))}</h1>
    <p>{html.escape(company_card_line(company['title']))}</p>
    <div class="meta-line">
      <span>{html.escape(company['first_seen'])} - {html.escape(company['last_seen'])}</span>
      <span>{html.escape(company.get('relationship',''))}</span>
    </div>
    {external_links_html(company['title'])}
  </header>
  <section class="detail-grid">
    <div class="paper-panel">
      <h2>案例时间线</h2>
      <ol class="evolution-list">{timeline}</ol>
    </div>
    <div class="paper-panel">
      <h2>验证了哪些概念</h2>
      <div class="tag-row">{tag_links(case.get('validated_concepts', []))}</div>
      <h2>相关人物</h2>
      <div class="tag-row">{tag_links(case.get('related_people', []), 'person')}</div>
    </div>
  </section>
  <section class="paper-panel">
    <h2>关键原话</h2>
    {quotes}
  </section>
  {f'''<section class="paper-panel source-list">
    <h2>资料来源</h2>
    <ul>{source_links_html}</ul>
  </section>''' if source_links_html else ''}
  <section class="paper-panel article-body">
    {md_to_html(strip_source_sections(company['body']))}
  </section>
</article>
"""


def people_page() -> str:
    cards = "".join(
        f"""<a class="archive-card" href="/person/{p['slug']}.html">
          <span>{html.escape(p['category'])}</span>
          <h3>{html.escape(clean_title(p['title']))}</h3>
          <p>{html.escape(person_card_line(p['title'], p.get('relationship','')))}</p>
          <em>查看关系</em>
        </a>"""
        for p in sorted(people, key=lambda x: x["mentioned_count"], reverse=True)
    )
    return f"""
<section class="page-hero compact">
  <p class="eyebrow">人物关系</p>
  <h1>人物关系</h1>
</section>
<div class="archive-grid">{cards}</div>
"""


def person_page(person: dict[str, Any]) -> str:
    sources = [cite_html(s) for s in source_candidates_from_body(person["body"]) if is_packable_source(s)]
    source_items = "".join(f"<li>{s}</li>" for s in sources if s)
    source_block = f"<section class='paper-panel source-list'><h2>资料来源</h2><ul>{source_items}</ul></section>" if source_items else ""
    return f"""
<article class="detail-page">
  <header class="detail-header">
    <p class="eyebrow">{html.escape(person['category'])}</p>
    <h1>{html.escape(clean_title(person['title']))}</h1>
    <div class="meta-line"><span>{person['mentioned_count']} 次提及</span><span>{html.escape(person['first_seen'])} - {html.escape(person['last_seen'])}</span></div>
    {external_links_html(person['title'])}
  </header>
  {source_block}
  <section class="paper-panel article-body">{md_to_html(strip_source_sections(person['body']))}</section>
</article>
"""


def sdl_page() -> str:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in sdl_items:
        groups[item["category"] or "不为清单"].append(item)
    sections = ""
    for category in ["投资不为清单", "企业经营不为清单", "人生/认知不为清单", "不为清单"]:
        group = groups.get(category)
        if not group:
            continue
        cards = "".join(
            f"""<a class="sdl-card" href="/stop-doing/{s['slug']}.html">
              <span>#{s['sdl_number']}</span>
              <h3>{html.escape(clean_title(s['title']))}</h3>
              <p>{html.escape(sdl_summary(s))}</p>
              <small>{html.escape(s['first_seen'])} 起 · {s['mentioned_count']} 次提及</small>
            </a>"""
            for s in sorted(group, key=lambda x: int(x["sdl_number"] or 0))
        )
        sections += f"<section class='sdl-section'><h2>{html.escape(category)}</h2><div class='sdl-grid'>{cards}</div></section>"
    lead_quote = quote_data.get("today_pool", [{}])[6] if len(quote_data.get("today_pool", [])) > 6 else {}
    return f"""
<section class="page-hero compact">
  <p class="eyebrow">Stop Doing List</p>
  <h1>不为清单。</h1>
  <p>Stop Doing List：把确定不能做的事写下来，少犯大错。</p>
</section>
<section class="paper-panel sdl-lead">
  <blockquote>{html.escape(lead_quote.get('text', ''))}</blockquote>
  <p>{cite_html(lead_quote.get('source', ''), lead_quote.get('text', ''), lead_quote.get('date', '')) if lead_quote else ''}</p>
</section>
{sections}
"""


def sdl_item_page(item: dict[str, Any]) -> str:
    quote = first_blockquote(item["body"])
    why = (
        section(item["body"], f"为什么「{clean_title(item['title'])}」是第一戒律？")
        or section(item["body"], f"为什么「{clean_title(item['title'])}」是铁律？")
        or section(item["body"], "核心要义")
    )
    lesson = section(item["body"], "血的教训")
    quotes = section(item["body"], "核心语录")
    timeline = section(item["body"], "时间线")
    source_block = sdl_source_block(item)
    return f"""
<article class="detail-page">
  <header class="detail-header">
    <p class="eyebrow">不为清单 #{item['sdl_number']}</p>
    <h1>{html.escape(clean_title(item['title']))}</h1>
    <div class="meta-line"><span>{html.escape(item['category'])}</span><span>{item['mentioned_count']} 次提及</span><span>{html.escape(item['severity'])}</span></div>
  </header>
  {f'<section class="paper-panel"><blockquote class="quote-card"><p>{md_inline(quote)}</p></blockquote></section>' if quote else ''}
  {f'<section class="paper-panel article-body"><h2>核心含义</h2>{md_to_html(why)}</section>' if why else ''}
  {f'<section class="paper-panel article-body"><h2>对应教训</h2>{md_to_html(lesson)}</section>' if lesson else ''}
  {f'<section class="paper-panel article-body"><h2>关键原话</h2>{md_to_html(quotes)}</section>' if quotes else ''}
  {f'<section class="paper-panel article-body"><h2>时间线</h2>{md_to_html(timeline)}</section>' if timeline else ''}
  <section class="related-block"><h2>关联阅读</h2><div class="tag-row">{tag_links(item.get('related_concepts', []))}</div></section>
  {source_block}
</article>
"""


def graph_page() -> str:
    return """
<section class="page-hero compact">
  <p class="eyebrow">知识图谱</p>
  <h1>关系索引</h1>
  <p>按节点查看一跳关系。</p>
</section>
<section class="paper-panel">
  <div class="graph-tools">
    <input id="graph-search" type="search" placeholder="搜索概念、企业、人物" autocomplete="off">
    <div class="graph-tabs" role="tablist">
      <button class="active" data-filter="all">全部</button>
      <button data-filter="concept">概念</button>
      <button data-filter="case">企业/案例</button>
      <button data-filter="entity">人物/实体</button>
    </div>
  </div>
  <div id="graph-list" class="graph-list"></div>
</section>
<script src="/graph.js"></script>
"""


def source_page(info: dict[str, Any]) -> str:
    path = info.get("path")
    if path and Path(path).exists():
        fm, body = parse_md(Path(path))
        body_html = source_body_html(info, body)
    else:
        body_html = ""
    excerpts = "".join(
        f"<blockquote class='quote-card'><p>{html.escape(excerpt)}</p></blockquote>"
        for excerpt in info.get("excerpts", [])[:12]
    )
    excerpt_section = f"<section class='paper-panel'><h2>本站引用摘录</h2>{excerpts}</section>" if excerpts else ""
    body_section = body_html
    return f"""
<article class="detail-page source-page">
  <header class="detail-header">
    <p class="eyebrow">资料来源</p>
    <h1>{html.escape(info['title'])}</h1>
    <div class="meta-line">
      {f'<span>{html.escape(info["date"])}</span>' if info.get('date') else ''}
      <span>{html.escape(source_type(info))}</span>
    </div>
  </header>
  {excerpt_section}
  {body_section}
</article>
"""


def write_source_pages() -> None:
    for event in events_data["events"]:
        for source in event.get("sources", []):
            if is_packable_source(source):
                register_source(source)
    source_registry_filtered = {source: info for source, info in source_registry.items() if source_has_content(info)}
    for source, info in list(source_registry_filtered.items()):
        path = info["url"].lstrip("/")
        write_page(path, info["title"], source_page(info), "")
    cards = "".join(
        f"""<a class="archive-card" href="{info['url']}">
          <span>{html.escape(info.get('date') or source_type(info))}</span>
          <h3>{html.escape(info['title'])}</h3>
          <p>{html.escape(source_type(info))}</p>
        </a>"""
        for info in sorted(source_registry_filtered.values(), key=lambda x: (x.get("date") or "9999", x["title"]))
    )
    write_page(
        "sources/index.html",
        "资料来源",
        f"""<section class="page-hero compact"><p class="eyebrow">资料来源</p><h1>引用来源</h1><p>年表、概念页和企业页引用到的公开材料。</p></section><div class="archive-grid">{cards}</div>""",
        "",
    )


def build_search_index() -> None:
    entries = []
    for group, label, prefix in [
        (concepts, "概念", "concept"),
        (companies, "企业", "company"),
        (people, "人物", "person"),
        (sdl_items, "不为清单", "stop-doing"),
    ]:
        for item in group:
            entries.append(
                {
                    "t": clean_title(item["title"]),
                    "y": label,
                    "p": f"/{prefix}/{item['slug']}.html",
                    "b": re.sub(r"\s+", " ", item["body"])[:700],
                }
            )
    for info in source_registry.values():
        if not source_has_content(info):
            continue
        entries.append(
            {
                "t": info["title"],
                "y": "资料来源",
                "p": info["url"],
                "b": " ".join(info.get("excerpts", []))[:700],
            }
        )
    (SITE_DIR / "search-index.json").write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")


def copy_data() -> None:
    data_dir = SITE_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    for name in ["timeline-index.json", "concept-frequency.json"]:
        shutil.copyfile(ANALYSIS_DIR / name, data_dir / name)


def main() -> None:
    for folder in ["concept", "company", "person", "stop-doing", "sources", "data"]:
        shutil.rmtree(SITE_DIR / folder, ignore_errors=True)
        (SITE_DIR / folder).mkdir(parents=True, exist_ok=True)
    copy_data()
    write_page("index.html", "首页", home_page(), "home")
    write_page("timeline.html", "思想年表", timeline_page(), "timeline")
    write_page("concepts.html", "核心概念", concepts_page(), "concepts")
    for concept in concepts:
        write_page(f"concept/{concept['slug']}.html", clean_title(concept["title"]), concept_page(concept), "concepts")
    write_page("companies.html", "企业档案", companies_page(), "companies")
    for company in companies:
        write_page(f"company/{company['slug']}.html", clean_title(company["title"]), company_page(company), "companies")
    write_page("people.html", "人物关系", people_page(), "people")
    for person in people:
        write_page(f"person/{person['slug']}.html", clean_title(person["title"]), person_page(person), "people")
    write_page("stop-doing.html", "不为清单", sdl_page(), "sdl")
    for item in sdl_items:
        write_page(f"stop-doing/{item['slug']}.html", item["title"], sdl_item_page(item), "sdl")
    write_page("graph.html", "知识图谱", graph_page(), "graph")
    write_source_pages()
    build_search_index()
    print(f"Built {SITE_DIR}")


if __name__ == "__main__":
    main()
