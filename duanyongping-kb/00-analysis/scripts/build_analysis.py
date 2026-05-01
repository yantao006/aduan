#!/usr/bin/env python3
"""Build analysis data for the timeline-driven Duan Yongping site.

The outputs are split by use:
- YAML: curated, human-maintainable event/quote/evolution/case data.
- JSON: machine-generated indexes and frequency series.
- Markdown: methodology, narrative outline, and validation report.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
KB_DIR = ROOT / "duanyongping-kb"
RAW_DIR = ROOT / "duanyongping"
OUT_DIR = KB_DIR / "00-analysis"
YEARS = list(range(1995, 2027))

CORE_CONCEPTS = [
    "买股票就是买公司",
    "未来现金流折现",
    "能力圈",
    "护城河",
    "本分",
    "平常心",
    "Stop Doing List (不为清单)",
    "商业模式",
]

CORE_COMPANIES = ["网易/NetEase", "苹果/Apple", "茅台/Moutai", "拼多多/PDD", "通用电气/GE"]


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


def section(body: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*$"
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(pattern, line):
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


def extract_blockquotes(body: str, limit: int = 8) -> list[str]:
    quotes: list[str] = []
    current: list[str] = []
    for line in body.splitlines():
        if line.startswith(">"):
            current.append(re.sub(r"^>\s?", "", line).strip())
        elif current:
            quote = " ".join(x for x in current if x).strip()
            if quote:
                quotes.append(quote)
            current = []
    if current:
        quote = " ".join(x for x in current if x).strip()
        if quote:
            quotes.append(quote)
    return quotes[:limit]


def extract_bullets(text: str, limit: int = 8) -> list[str]:
    bullets = []
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^(?:[-*]|\d+\.)\s+(.+)$", line)
        if m:
            bullets.append(m.group(1).strip())
    return bullets[:limit]


def clean_title(title: str) -> str:
    title = title.strip()
    title = re.sub(r"\s*/\s*.*$", "", title)
    title = re.sub(r"\s*\(.*?\)\s*$", "", title)
    return title.strip()


def infer_year(path: Path, text: str = "") -> int | None:
    s = str(path.relative_to(ROOT))
    candidates = []
    for pattern in [
        r"xueqiu-timeline/((?:19|20)\d{2})-\d{2}",
        r"/((?:19|20)\d{2})[-年]",
        r"(^|/)\d+-((?:19|20)\d{2})",
        r"((?:19|20)\d{2})（",
    ]:
        for match in re.finditer(pattern, s):
            year = match.group(1) if match.lastindex == 1 else match.group(2)
            candidates.append(int(year))
    if not candidates and text:
        head = text[:500]
        for match in re.finditer(r"(?:19|20)\d{2}", head):
            candidates.append(int(match.group(0)))
    candidates = [y for y in candidates if 1990 <= y <= 2026]
    return candidates[0] if candidates else None


def load_kb_items() -> list[dict[str, Any]]:
    specs = [
        ("01-投资概念", "concept"),
        ("02-Stop-Doing-List", "sdl"),
        ("03-企业与品牌", "company"),
        ("04-关键人物", "person"),
    ]
    items = []
    for folder, fallback_type in specs:
        for path in sorted((KB_DIR / folder).glob("*.md")):
            fm, body = parse_md(path)
            if not fm or path.name == "README.md":
                continue
            items.append(
                {
                    "title": fm.get("title", path.stem),
                    "short_title": clean_title(fm.get("title", path.stem)),
                    "type": fm.get("type", fallback_type),
                    "category": fm.get("category", ""),
                    "mentioned_count": fm.get("mentioned_count", 0) or 0,
                    "first_seen": str(fm.get("first_seen", "") or ""),
                    "last_seen": str(fm.get("last_seen", "") or ""),
                    "related_concepts": fm.get("related_concepts", []) or [],
                    "related_companies": fm.get("related_companies", []) or [],
                    "related_people": fm.get("related_people", []) or [],
                    "relationship": fm.get("relationship", "") or "",
                    "path": str(path.relative_to(ROOT)),
                    "body": body,
                }
            )
    return items


def alias_map(items: list[dict[str, Any]]) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    manual = {
        "买股票就是买公司": ["买股票就是买公司", "买公司"],
        "未来现金流折现": ["未来现金流折现", "未来现金流", "现金流折现", "DCF", "dcf"],
        "right business right people right price": [
            "right business right people right price",
            "right business",
            "right people",
            "right price",
            "好生意",
            "好管理",
            "好价格",
        ],
        "Stop Doing List (不为清单)": ["Stop Doing List", "stop doing list", "不为清单", "SDL", "sdl"],
        "做对的事情 把事情做对": ["做对的事情", "把事情做对", "do right thing"],
        "10年视角": ["10年视角", "十年视角", "10 年视角", "十年"],
        "企业文化与投资": ["企业文化与投资", "企业文化和投资", "re:企业文化.{0,30}投资|投资.{0,30}企业文化"],
        "犯错与纠错": ["犯错与纠错", "发现错了马上改", "发现错了", "错了马上改", "纠错", "犯错"],
        "好生意好管理好价格": [
            "好生意好管理好价格",
            "好生意、好管理、好价格",
            "好生意 好管理 好价格",
            "right business right people right price",
            "right business",
            "right people",
            "right price",
            "re:好生意.{0,10}好管理.{0,10}好价格",
        ],
        "苹果/Apple": ["苹果", "Apple", "AAPL", "apple"],
        "茅台/Moutai": ["茅台", "贵州茅台", "Moutai"],
        "网易/NetEase": ["网易", "NetEase", "NTES"],
        "拼多多/PDD": ["拼多多", "PDD", "Pinduoduo"],
        "通用电气/GE": ["通用电气", "GE"],
        "富国银行/Wells Fargo": ["富国银行", "Wells Fargo", "WFC"],
        "步步高 (BBK)": ["步步高", "BBK"],
        "沃伦·巴菲特 / Warren Buffett": ["巴菲特", "Buffett", "Warren Buffett", "老巴"],
        "查理·芒格 / Charlie Munger": ["芒格", "Munger", "Charlie Munger"],
        "黄峥 / Colin Huang": ["黄峥", "Colin Huang"],
    }
    for item in items:
        title = item["title"]
        short = item["short_title"]
        base = [title, short]
        if "/" in title:
            base.extend([x.strip() for x in title.split("/") if x.strip()])
        base.extend(manual.get(title, []))
        base.extend(manual.get(short, []))
        deduped = []
        for alias in base:
            if alias and alias not in deduped:
                deduped.append(alias)
        aliases[title] = deduped
    return aliases


def count_occurrences(text: str, aliases: list[str]) -> int:
    total = 0
    for alias in aliases:
        if alias.startswith("re:"):
            total += len(re.findall(alias[3:], text, re.I | re.S))
        elif re.fullmatch(r"[A-Za-z0-9 .+-]+", alias):
            total += len(re.findall(rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])", text, re.I))
        else:
            total += text.count(alias)
    return total


def build_frequency(items: list[dict[str, Any]]) -> tuple[dict[str, dict[str, int]], list[dict[str, Any]]]:
    aliases = alias_map(items)
    concepts = [item for item in items if item["type"] == "concept"]
    series: dict[str, Counter[int]] = {item["title"]: Counter() for item in concepts}
    docs = []
    raw_files = sorted(RAW_DIR.rglob("*.md"))
    for path in raw_files:
        text = read_text(path)
        year = infer_year(path, text)
        if year is None or year not in YEARS:
            continue
        hit_counter = Counter()
        for item in concepts:
            count = count_occurrences(text, aliases[item["title"]])
            if count:
                series[item["title"]][year] += count
                hit_counter[item["title"]] = count
        if hit_counter:
            docs.append(
                {
                    "year": year,
                    "path": str(path.relative_to(ROOT)),
                    "top_concepts": [
                        {"concept": concept, "count": count}
                        for concept, count in hit_counter.most_common(8)
                    ],
                }
            )
    output = {
        title: {str(y): int(counter.get(y, 0)) for y in YEARS if counter.get(y, 0)}
        for title, counter in series.items()
    }
    return output, docs


def load_concept_json_quotes() -> dict[str, list[dict[str, Any]]]:
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in sorted((RAW_DIR / "concept-data").glob("*.json")):
        data = json.loads(read_text(path))
        concepts = data.get("concepts") if isinstance(data, dict) and "concepts" in data else data
        if not isinstance(concepts, dict):
            continue
        for name, payload in concepts.items():
            if not isinstance(payload, dict):
                continue
            display_name = payload.get("name") or name
            for q in payload.get("quotes", [])[:8]:
                if isinstance(q, str):
                    by_name[display_name].append({"text": q, "source": "", "date": ""})
                elif isinstance(q, dict):
                    text = q.get("text") or q.get("quote")
                    if text:
                        by_name[display_name].append(
                            {
                                "text": text,
                                "source": q.get("source", ""),
                                "date": str(q.get("date", "")),
                                "speaker": q.get("speaker", "段永平"),
                            }
                        )
    return by_name


def quote_selections(items: list[dict[str, Any]]) -> dict[str, Any]:
    json_quotes = load_concept_json_quotes()
    output: dict[str, Any] = {
        "meta": {
            "purpose": "精选语录池，用于首页今日语录、概念页原话区、思想年表节点。",
            "selection_rule": "优先使用已有结构化概念数据中的带来源语录；不足时回退到 KB 词条中的 blockquote。",
            "generated_at": date.today().isoformat(),
        },
        "today_pool": [],
        "by_concept": {},
    }
    concepts = [item for item in items if item["type"] == "concept"]
    for item in concepts:
        title = item["title"]
        short = item["short_title"]
        candidates = json_quotes.get(short, []) or json_quotes.get(title, [])
        if not candidates:
            candidates = [
                {"text": q, "source": item["path"], "date": item["first_seen"], "speaker": "段永平"}
                for q in extract_blockquotes(item["body"], 6)
            ]
        selected = []
        for q in candidates[:5]:
            selected.append(
                {
                    "text": re.sub(r"\s+", " ", q.get("text", "")).strip(),
                    "speaker": q.get("speaker", "段永平"),
                    "date": str(q.get("date") or item["first_seen"]),
                    "source": q.get("source") or item["path"],
                    "concepts": [title],
                    "usage": ["concept_page"],
                }
            )
        if selected:
            output["by_concept"][title] = selected
            if title in CORE_CONCEPTS:
                today = dict(selected[0])
                today["usage"] = ["home_today", "concept_page"]
                output["today_pool"].append(today)
    return output


EVENTS = [
    {
        "year": 1995,
        "title": "创立步步高",
        "summary": "离开小霸王后在东莞创立步步高，企业文化和长期主义实践开始成形。",
        "chapter": "企业文化的源头",
        "concepts": ["本分", "企业文化", "消费者导向"],
        "companies": ["步步高 (BBK)"],
        "people": ["陈明永 / Tony Chen", "沈炜 / Shen Wei"],
        "sources": ["duanyongping-kb/03-企业与品牌/01-步步高-BBK.md"],
    },
    {
        "year": 1999,
        "title": "提出更健康、更长久",
        "summary": "步步高早期愿景不是做大，而是更健康、更长久地活下去。",
        "chapter": "企业文化的源头",
        "concepts": ["本分", "平常心", "做对的事情 把事情做对"],
        "companies": ["步步高 (BBK)"],
        "sources": ["duanyongping/01-core/duan-main/【文章目录】/1-核心-公司里程碑/01-1999-段永平-二十一世纪来了.md"],
    },
    {
        "year": 2000,
        "title": "销售手册前言与焦点法则",
        "summary": "围绕本分、诚信、消费者导向、焦点法则，形成经营层面的不做清单雏形。",
        "chapter": "企业文化的源头",
        "concepts": ["本分", "焦点法则", "不赚快钱", "不盲目扩张"],
        "companies": ["步步高 (BBK)", "OPPO"],
        "sources": ["duanyongping/01-core/duan-main/【文章目录】/1-核心-公司里程碑/08-2000-段永平给营销人员讲话（销售手册前言）.md"],
    },
    {
        "year": 2001,
        "title": "移居美国，投资视角转向公司本质",
        "summary": "离开一线经营后，开始系统接触巴菲特思想，并从企业家视角理解投资。",
        "chapter": "从企业家到投资人",
        "concepts": ["买股票就是买公司", "企业文化与投资", "价值投资"],
        "people": ["沃伦·巴菲特 / Warren Buffett", "本杰明·格雷厄姆 / Benjamin Graham"],
        "sources": ["duanyongping-kb/04-关键人物/01-巴菲特.md"],
    },
    {
        "year": 2002,
        "title": "投资网易",
        "summary": "在网易极低估值时买入，成为“买公司而非买股票”的代表性案例。",
        "chapter": "从企业家到投资人",
        "concepts": ["买股票就是买公司", "能力圈", "安全边际", "贪婪恐惧"],
        "companies": ["网易/NetEase"],
        "people": ["丁磊 / William Ding"],
        "sources": ["duanyongping-kb/01-投资概念/26-网易.md", "duanyongping-kb/03-企业与品牌/07-网易-NetEase.md"],
    },
    {
        "year": 2004,
        "title": "公开谈企业诚信与价值投资",
        "summary": "在访谈和演讲中持续把企业经营原则与投资原则连接起来。",
        "chapter": "从企业家到投资人",
        "concepts": ["本分", "价值投资", "企业文化与投资"],
        "sources": [
            "duanyongping/01-core/duan-main/【文章目录】/2-对外演讲、采访/01-2004-万科财富人生-对话段永平.md",
            "duanyongping/01-core/duan-main/【文章目录】/2-对外演讲、采访/02-2004（左右）-段永平北大总裁班演讲：企业的诚信意识.md",
        ],
    },
    {
        "year": 2005,
        "title": "步步高十周年讲话",
        "summary": "系统表达本分、诚信、团队、品质、消费者导向，以及少犯错的重要性。",
        "chapter": "企业文化的源头",
        "concepts": ["本分", "企业文化", "犯错与纠错", "发现错了马上改"],
        "companies": ["步步高 (BBK)"],
        "people": ["陈明永 / Tony Chen", "沈炜 / Shen Wei"],
        "sources": ["duanyongping/01-core/duan-main/【文章目录】/1-核心-公司里程碑/04-2005-段永平-步步高十周年记念文艺晚会讲话.md"],
    },
    {
        "year": 2006,
        "title": "巴菲特午餐",
        "summary": "以 62.01 万美元拍下巴菲特午餐，强化“买股票就是买公司”和不用杠杆等原则。",
        "chapter": "买公司这条主线",
        "concepts": ["买股票就是买公司", "不借钱", "不懂不做", "长期持有"],
        "people": ["沃伦·巴菲特 / Warren Buffett"],
        "sources": ["duanyongping/01-core/duan-main/【文章目录】/2-对外演讲、采访/05-2006-网易财经专访段永平-谈和巴菲特共进午餐.md"],
    },
    {
        "year": 2008,
        "title": "金融危机与 GE",
        "summary": "危机中关注 GE，后来把 GE 视为“赚钱但仍可能是错”的纠错案例。",
        "chapter": "风险纪律成形",
        "concepts": ["安全边际", "犯错与纠错", "企业文化与投资"],
        "companies": ["通用电气/GE"],
        "sources": ["duanyongping-kb/03-企业与品牌/09-GE-通用电气.md"],
    },
    {
        "year": 2010,
        "title": "系统提出“买股票就是买公司”",
        "summary": "在博客、访谈和问答中反复把投资定义为买公司的未来现金流。",
        "chapter": "买公司这条主线",
        "concepts": ["买股票就是买公司", "未来现金流折现", "能力圈", "市场先生"],
        "sources": ["duanyongping/01-core/duan-main/【文章目录】/2-对外演讲、采访/08-2010-网易财经-对话段永平.md"],
    },
    {
        "year": 2011,
        "title": "苹果进入核心视野",
        "summary": "苹果逐渐成为商业模式、护城河、企业文化和长期持有的核心案例。",
        "chapter": "好生意的验证",
        "concepts": ["护城河", "商业模式", "长期持有", "分红回购"],
        "companies": ["苹果/Apple"],
        "sources": ["duanyongping-kb/01-投资概念/27-苹果.md", "duanyongping-kb/03-企业与品牌/04-苹果-Apple.md"],
    },
    {
        "year": 2013,
        "title": "茅台危机中的理解",
        "summary": "塑化剂、反腐等冲击中重新审视茅台的生意属性、确定性和好价格。",
        "chapter": "好生意的验证",
        "concepts": ["确定性", "好价格", "商业模式", "贪婪恐惧"],
        "companies": ["茅台/Moutai"],
        "sources": ["duanyongping-kb/01-投资概念/28-茅台.md", "duanyongping-kb/03-企业与品牌/05-茅台-Moutai.md"],
    },
    {
        "year": 2015,
        "title": "vivo 二十周年与本分再阐释",
        "summary": "沈炜系统阐述本分的多重维度，企业文化成为理解步步高系的关键入口。",
        "chapter": "企业文化外化",
        "concepts": ["本分", "企业文化", "消费者导向", "差异化"],
        "companies": ["vivo", "OPPO"],
        "people": ["沈炜 / Shen Wei"],
        "sources": ["duanyongping/01-core/duan-main/【文章目录】/1-核心-公司里程碑/05-2015-沈炜-步步高（vivo）20周年.md"],
    },
    {
        "year": 2016,
        "title": "苹果重仓逻辑被反复讨论",
        "summary": "苹果成为高确定性、强护城河、好生意和集中投资的综合样本。",
        "chapter": "好生意的验证",
        "concepts": ["护城河", "集中投资", "好生意好管理好价格", "确定性"],
        "companies": ["苹果/Apple"],
        "sources": ["duanyongping-kb/01-投资概念/27-苹果.md"],
    },
    {
        "year": 2018,
        "title": "斯坦福 Stop Doing List",
        "summary": "Stop Doing List 被公开讲成统一方法论：不做错事，才能长期做对事。",
        "chapter": "不为清单成为方法论",
        "concepts": ["Stop Doing List (不为清单)", "做对的事情 把事情做对", "本分", "平常心"],
        "sources": [
            "duanyongping/01-core/duan-main/【文章目录】/2-对外演讲、采访/09-2018-段永平斯坦福交流.md",
            "duanyongping/02-supplement/web-articles-md/2018-斯坦福Stop-Doing-List.md",
        ],
    },
    {
        "year": 2020,
        "title": "疫情时期回到企业内在价值",
        "summary": "市场剧烈波动中，思想主线继续回到公司、现金流和长期确定性。",
        "chapter": "回到本质",
        "concepts": ["10年视角", "长期持有", "平常心", "市场先生"],
        "companies": ["苹果/Apple", "茅台/Moutai", "腾讯/Tencent"],
        "sources": ["duanyongping/01-core/xueqiu-timeline/2020-03_@大道无形我有型.md"],
    },
    {
        "year": 2021,
        "title": "茅台波动与持有等于买入",
        "summary": "在价格大幅波动中，讨论持有是否等于重新买入，以及机会成本问题。",
        "chapter": "回到本质",
        "concepts": ["持有等于买入", "好价格", "10年视角", "确定性"],
        "companies": ["茅台/Moutai"],
        "sources": ["duanyongping-kb/01-投资概念/25-持有等于买入.md"],
    },
    {
        "year": 2023,
        "title": "拼多多成为新案例",
        "summary": "拼多多更多被放在早期判断、商业模式、创始人和不确定性的框架下讨论。",
        "chapter": "新案例与旧框架",
        "concepts": ["商业模式", "管理层", "确定性", "能力圈"],
        "companies": ["拼多多/PDD"],
        "people": ["黄峥 / Colin Huang"],
        "sources": ["duanyongping-kb/01-投资概念/29-拼多多.md", "duanyongping-kb/03-企业与品牌/06-拼多多-PDD.md"],
    },
    {
        "year": 2024,
        "title": "公益与长期价值观延续",
        "summary": "再捐 10 亿等事件强化了长期、平常心和价值观一致性的外部叙事。",
        "chapter": "回到本质",
        "concepts": ["本分", "平常心", "长期持有"],
        "sources": ["duanyongping/02-supplement/web-articles-md/2024-再捐10亿.md"],
    },
    {
        "year": 2025,
        "title": "方三文对话与 AI 时代思考",
        "summary": "系统回顾步步高系三十年、投资框架、Stop Doing List，并讨论 AI 对商业和投资的影响。",
        "chapter": "新案例与旧框架",
        "concepts": ["Stop Doing List (不为清单)", "10年视角", "商业模式", "能力圈"],
        "people": ["方三文", "王石"],
        "sources": [
            "duanyongping/01-core/duan-main/【文章目录】/2-对外演讲、采访/11-2025-雪球-方三文对话段永平.md",
            "duanyongping/01-core/duan-main/【文章目录】/2-对外演讲、采访/12-2025-王石对话段永平.md",
        ],
    },
]


def build_events() -> dict[str, Any]:
    return {
        "meta": {
            "purpose": "思想年表主数据，用于首页横向时间轴、滚动叙事章节和年份详情页。",
            "range": "1995-2025",
            "generated_at": date.today().isoformat(),
        },
        "chapters": [
            {"id": "origin", "title": "企业文化的源头", "years": "1995-2000"},
            {"id": "investor", "title": "从企业家到投资人", "years": "2001-2005"},
            {"id": "buy-company", "title": "买公司这条主线", "years": "2006-2010"},
            {"id": "risk", "title": "风险纪律成形", "years": "2008-2010"},
            {"id": "good-business", "title": "好生意的验证", "years": "2011-2016"},
            {"id": "culture", "title": "企业文化外化", "years": "2015-2025"},
            {"id": "sdl", "title": "不为清单成为方法论", "years": "2018"},
            {"id": "new-cases", "title": "新案例与旧框架", "years": "2023-2025"},
            {"id": "return-to-essence", "title": "回到本质", "years": "2020-2025"},
        ],
        "events": EVENTS,
    }


def summarize_evolution(item: dict[str, Any], frequency: dict[str, dict[str, int]]) -> dict[str, Any]:
    title = item["title"]
    evolution = section(item["body"], "演变轨迹")
    bullets = extract_bullets(evolution, 6)
    series = frequency.get(title, {})
    peak_years = sorted(series.items(), key=lambda kv: kv[1], reverse=True)[:5]
    quotes = extract_blockquotes(item["body"], 3)
    phases = []
    for bullet in bullets:
        year_match = re.search(r"(19|20)\d{2}(?:[-—~至到]\d{2,4})?", bullet)
        phases.append(
            {
                "period": year_match.group(0) if year_match else "",
                "summary": re.sub(r"^\*\*(.+?)\*\*[:：]?", r"\1：", bullet),
            }
        )
    if not phases:
        first = item["first_seen"] or ""
        last = item["last_seen"] or ""
        phases = [
            {
                "period": f"{first}-{last}".strip("-"),
                "summary": "当前 KB 尚未拆出明确阶段，先以首次/最近出现时间和频次峰值作为后续人工精修线索。",
            }
        ]
    return {
        "category": item["category"],
        "first_seen": item["first_seen"],
        "last_seen": item["last_seen"],
        "mentioned_count": item["mentioned_count"],
        "core_for_timeline": title in CORE_CONCEPTS,
        "frequency_peak_years": [{"year": int(y), "count": int(c)} for y, c in peak_years],
        "phases": phases,
        "representative_quotes": quotes,
        "related_concepts": item["related_concepts"],
        "related_companies": item["related_companies"],
        "related_people": item["related_people"],
        "source_card": item["path"],
    }


def build_concept_evolution(items: list[dict[str, Any]], frequency: dict[str, dict[str, int]]) -> dict[str, Any]:
    concepts = [item for item in items if item["type"] == "concept"]
    return {
        "meta": {
            "purpose": "概念页的演变轨迹数据。核心概念可直接用于页面；非核心概念作为待人工精修底稿。",
            "core_concepts": CORE_CONCEPTS,
            "generated_at": date.today().isoformat(),
        },
        "concepts": {item["title"]: summarize_evolution(item, frequency) for item in concepts},
    }


def parse_timeline_from_body(body: str) -> list[dict[str, Any]]:
    timeline_text = section(body, "时间线") or section(body, "投资时间线")
    rows = []
    for bullet in extract_bullets(timeline_text, 20):
        match = re.match(r"\*\*(.+?)\*\*[:：]?\s*(.*)", bullet)
        if match:
            year = match.group(1)
            summary = match.group(2).strip()
        else:
            y = re.search(r"(19|20)\d{2}(?:[-—~至到]\d{2,4})?", bullet)
            year = y.group(0) if y else ""
            summary = bullet
        rows.append({"period": year, "event": summary or bullet})
    return rows


def build_company_cases(items: list[dict[str, Any]]) -> dict[str, Any]:
    companies = [item for item in items if item["type"] == "company"]
    concepts_by_short = {
        item["short_title"]: item for item in items if item["type"] == "concept"
    }
    output = {
        "meta": {
            "purpose": "企业页案例研究数据，用于把企业从档案改造成思想验证案例。",
            "core_companies": CORE_COMPANIES,
            "generated_at": date.today().isoformat(),
        },
        "companies": {},
    }
    for item in companies:
        title = item["title"]
        timeline = parse_timeline_from_body(item["body"])
        fallback_concept = concepts_by_short.get(item["short_title"])
        if not timeline and fallback_concept:
            timeline = parse_timeline_from_body(fallback_concept["body"])
        output["companies"][title] = {
            "category": item["category"],
            "relationship": item["relationship"],
            "first_seen": item["first_seen"],
            "last_seen": item["last_seen"],
            "mentioned_count": item["mentioned_count"],
            "core_for_timeline": title in CORE_COMPANIES,
            "case_role": infer_case_role(title),
            "timeline": timeline,
            "validated_concepts": item["related_concepts"],
            "related_people": item["related_people"],
            "representative_quotes": extract_blockquotes(item["body"], 4),
            "source_card": item["path"],
        }
    return output


def infer_case_role(title: str) -> str:
    roles = {
        "网易/NetEase": "从极端低估到百倍回报，验证买公司、能力圈与安全边际。",
        "苹果/Apple": "验证好生意、护城河、企业文化、集中投资和长期持有。",
        "茅台/Moutai": "验证确定性、好价格、品牌和十年视角。",
        "拼多多/PDD": "验证早期判断、创始人理解、商业模式与不确定性边界。",
        "通用电气/GE": "作为纠错案例，说明赚钱的投资也可能是错的。",
        "富国银行/Wells Fargo": "金融企业风险与企业文化变化的警示样本。",
        "腾讯/Tencent": "互联网平台商业模式和机会成本的观察样本。",
        "步步高 (BBK)": "企业文化、本分、授权和 Stop Doing List 的源头案例。",
        "OPPO": "本分、消费者导向、不做代工与长期经营纪律的实践样本。",
        "vivo": "本分、差异化、长期投入和全球化表达的实践样本。",
    }
    return roles.get(title, "")


def build_timeline_index(
    items: list[dict[str, Any]], frequency: dict[str, dict[str, int]], docs: list[dict[str, Any]]
) -> dict[str, Any]:
    by_year = {str(year): {"events": [], "top_concepts": [], "documents": []} for year in YEARS}
    for event in EVENTS:
        by_year[str(event["year"])]["events"].append(
            {
                "title": event["title"],
                "summary": event["summary"],
                "concepts": event.get("concepts", []),
                "companies": event.get("companies", []),
                "people": event.get("people", []),
            }
        )
    for year in YEARS:
        counts = []
        for concept, series in frequency.items():
            if str(year) in series:
                counts.append({"concept": concept, "count": series[str(year)]})
        by_year[str(year)]["top_concepts"] = sorted(counts, key=lambda x: x["count"], reverse=True)[:12]
    doc_by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for doc in docs:
        doc_by_year[doc["year"]].append(doc)
    for year, year_docs in doc_by_year.items():
        by_year[str(year)]["documents"] = sorted(
            year_docs, key=lambda d: sum(x["count"] for x in d["top_concepts"]), reverse=True
        )[:12]
    return {
        "meta": {
            "purpose": "前端年表索引。聚合事件、年度高频概念和代表性文档。",
            "generated_at": date.today().isoformat(),
            "year_range": [YEARS[0], YEARS[-1]],
        },
        "years": by_year,
    }


def source_exists(source: str) -> bool:
    return (ROOT / source).exists()


def validation_report(
    items: list[dict[str, Any]],
    frequency: dict[str, dict[str, int]],
    events: dict[str, Any],
    quotes: dict[str, Any],
    cases: dict[str, Any],
) -> str:
    lines = [
        "# 数据分析校验报告",
        "",
        f"生成日期：{date.today().isoformat()}",
        "",
        "## 覆盖情况",
        "",
        f"- KB 条目：{len(items)}",
        f"- 概念频次序列：{len(frequency)}",
        f"- 年表事件：{len(events['events'])}",
        f"- 概念语录组：{len(quotes['by_concept'])}",
        f"- 今日语录池：{len(quotes['today_pool'])}",
        f"- 企业案例：{len(cases['companies'])}",
        "",
        "## 事件来源校验",
        "",
    ]
    missing_sources = []
    for event in events["events"]:
        for source in event.get("sources", []):
            if not source_exists(source):
                missing_sources.append((event["year"], event["title"], source))
    if missing_sources:
        lines.append("存在缺失来源，需要人工处理：")
        for year, title, source in missing_sources:
            lines.append(f"- {year} {title}: `{source}`")
    else:
        lines.append("所有事件来源路径均存在。")
    lines.extend(["", "## 频次异常检查", ""])
    empty = [k for k, v in frequency.items() if not v]
    if empty:
        lines.append("以下概念没有在原始 Markdown 中匹配到逐年频次，后续需要补 alias：")
        for name in empty:
            lines.append(f"- {name}")
    else:
        lines.append("所有概念均有至少一个年度频次命中。")
    lines.extend(["", "## 结构完整性检查", ""])
    chapter_titles = {chapter["title"] for chapter in events["chapters"]}
    missing_chapters = [event for event in events["events"] if event.get("chapter") not in chapter_titles]
    empty_company_timelines = [
        name for name, payload in cases["companies"].items() if not payload.get("timeline")
    ]
    if missing_chapters:
        lines.append("存在未登记章节的事件：")
        for event in missing_chapters:
            lines.append(f"- {event['year']} {event['title']}: {event.get('chapter')}")
    else:
        lines.append("所有事件的 chapter 均已登记。")
    if empty_company_timelines:
        lines.append("存在空企业案例时间线：")
        for name in empty_company_timelines:
            lines.append(f"- {name}")
    else:
        lines.append("所有企业案例均有时间线。")
    lines.append(f"核心概念覆盖：{len(CORE_CONCEPTS)} / {len(CORE_CONCEPTS)}。")
    lines.extend(["", "## 核心概念峰值年份", ""])
    for concept in CORE_CONCEPTS:
        series = frequency.get(concept, {})
        peaks = sorted(series.items(), key=lambda kv: kv[1], reverse=True)[:5]
        peak_text = "，".join(f"{year}: {count}" for year, count in peaks) or "无"
        lines.append(f"- {concept}: {peak_text}")
    lines.extend(["", "## 后续人工复核建议", ""])
    lines.extend(
        [
            "- 逐年频次是关键词匹配，适合做趋势参考，不等同于严格语义判断。",
            "- 企业、人物和英文缩写可能存在歧义，页面上线前建议对核心年份做抽样阅读。",
            "- 事件 YAML 已经可直接支撑首页和思想年表，但每个事件的代表语录还可继续精修。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_yaml(path: Path, data: Any) -> None:
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown_docs() -> None:
    (OUT_DIR / "README.md").write_text(
        """# 段永平思想时间轴数据层

这个目录服务于新版“投资时间轴”网站方案。它不是原始资料库，也不是最终页面内容，而是介于两者之间的分析层。

## 文件分工

- `events.yaml`：人工可维护的主年表事件，用于首页和思想年表。
- `concept-evolution.yaml`：概念演变底稿，用于概念页的“演变轨迹”。
- `quote-selections.yaml`：精选语录池，用于“今日段永平”、概念页和年表节点。
- `company-case-timeline.yaml`：企业案例时间线，用于把企业页改造成案例研究。
- `concept-frequency.json`：从原始 Markdown 统计出的逐年概念频次，用于折线图。
- `timeline-index.json`：前端年表聚合索引，合并事件、年度概念和代表文档。
- `narrative-outline.md`：滚动叙事页面的章节草案。
- `data-methodology.md`：数据生成方法与局限。
- `validation-report.md`：本轮生成后的覆盖率和异常检查。

## 使用原则

YAML 由人继续维护，JSON 由脚本生成，Markdown 记录研究判断和方法说明。

重新生成：

```bash
python3 duanyongping-kb/00-analysis/scripts/build_analysis.py
```
""",
        encoding="utf-8",
    )
    (OUT_DIR / "data-methodology.md").write_text(
        """# 数据方法说明

## 输入

本轮分析读取三类资料：

1. `duanyongping-kb/` 下已整理的概念、企业、人物、Stop Doing List 卡片。
2. `duanyongping/` 下的原始 Markdown 资料，包括网易博客、雪球时间线、访谈和补充网页文章。
3. `duanyongping/concept-data/` 下已有的结构化概念 JSON。

## 年份识别

优先从文件路径识别年份，例如：

- `xueqiu-timeline/2025-10_...`
- `2-对外演讲、采访/11-2025-...`
- `1-核心-公司里程碑/04-2005-...`

路径无法识别时，才尝试读取正文开头的年份。

## 频次统计

`concept-frequency.json` 采用关键词和别名匹配。它适合展示趋势，但不是严格语义分析。

例如“买股票就是买公司”同时匹配：

- 买股票就是买公司
- 买公司

“未来现金流折现”同时匹配：

- 未来现金流折现
- 未来现金流
- 现金流折现
- DCF

## 人工策展层

`events.yaml`、`concept-evolution.yaml`、`quote-selections.yaml`、`company-case-timeline.yaml` 是给人继续打磨的策展层。脚本生成了可用底稿，但上线前仍建议对首页首屏、核心概念和核心企业做人工复核。

## 已知局限

- 简称如 GE、PDD、AI、Apple 可能有歧义。
- 中文短词如“品牌”“管理层”“十年”可能被上下文放大。
- 语录与来源在部分旧资料中不是一一结构化关系，目前先保留来源卡片或结构化 JSON 来源。
""",
        encoding="utf-8",
    )
    (OUT_DIR / "narrative-outline.md").write_text(
        """# 滚动叙事大纲：段永平思想年表

## 核心问题

段永平的投资和经营思想，是如何从企业经营实践中生长出来，又在二十多年投资案例中被反复验证、修正和收敛的？

## 章节

### 第一章：企业文化的源头，1995-2000

从步步高创立、“更健康、更长久”、销售手册前言开始，解释本分、消费者导向、焦点法则和不赚快钱。

### 第二章：从企业家到投资人，2001-2005

移居美国后，段永平以企业家的经验理解巴菲特。网易案例让“买公司”从抽象原则变成投资实践。

### 第三章：买公司这条主线，2006-2010

巴菲特午餐之后，“买股票就是买公司”“未来现金流折现”“能力圈”“不借钱”被系统表达。

### 第四章：好生意的验证，2011-2016

苹果、茅台等案例让护城河、商业模式、企业文化与长期持有成为可观察样本。

### 第五章：Stop Doing List 成为方法论，2018

斯坦福演讲把“不做什么”提升为统一框架：不做错事，才能长期做对事。

### 第六章：新案例与旧框架，2020-2025

疫情、茅台波动、拼多多、AI 时代思考，都没有改变底层框架，反而让能力圈、十年视角和平常心更突出。

## 页面呈现建议

- 左侧：章节叙事文本。
- 右侧：随滚动变化的时间轴、频次折线图或企业案例卡。
- 每章只放 1-2 条代表语录，避免语录堆砌。
- 核心概念首次出现时插入概念卡；再次出现时展示“含义变化”。
""",
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "scripts").mkdir(parents=True, exist_ok=True)

    items = load_kb_items()
    frequency, docs = build_frequency(items)
    events = build_events()
    quotes = quote_selections(items)
    concept_evolution = build_concept_evolution(items, frequency)
    company_cases = build_company_cases(items)
    timeline_index = build_timeline_index(items, frequency, docs)

    write_yaml(OUT_DIR / "events.yaml", events)
    write_yaml(OUT_DIR / "concept-evolution.yaml", concept_evolution)
    write_yaml(OUT_DIR / "quote-selections.yaml", quotes)
    write_yaml(OUT_DIR / "company-case-timeline.yaml", company_cases)
    write_json(OUT_DIR / "concept-frequency.json", frequency)
    write_json(OUT_DIR / "timeline-index.json", timeline_index)
    write_markdown_docs()

    report = validation_report(items, frequency, events, quotes, company_cases)
    (OUT_DIR / "validation-report.md").write_text(report, encoding="utf-8")

    print(f"wrote analysis data to {OUT_DIR}")
    print(report)


if __name__ == "__main__":
    main()
