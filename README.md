# 段永平投资知识库

一个围绕段永平公开资料整理的中文投资思想知识库，包含原始资料归档、结构化知识卡片、分析数据层和静态网站。

网站主线不是简单收集语录，而是把段永平在企业经营、投资判断、Stop Doing List、不为清单、企业案例和人物关系中的公开表达，整理成可追溯、可跳转、可继续校验的研究型资料库。

## 项目内容

- **原始资料库**：雪球、网易博客、访谈、演讲、PDF、新闻报道、企业文化材料等。
- **结构化知识库**：投资概念、企业案例、关键人物、Stop Doing List 条目。
- **分析数据层**：思想年表、概念频次、概念演变、企业案例时间线、精选语录和来源校验。
- **静态网站**：首页、思想年表、核心概念、企业档案、人物关系、不为清单、知识图谱和资料来源页。

## 目录结构

```text
.
├── duanyongping/                 # 原始资料归档
│   ├── 01-core/                  # 核心资料：雪球、网易博客、访谈、公司里程碑
│   ├── 02-supplement/            # 补充网页文章、新闻报道等
│   ├── 03-pdfs/                  # PDF 资料
│   └── 99-references/            # 外部参考项目和辅助材料
│
├── duanyongping-kb/              # 结构化知识库
│   ├── 00-analysis/              # 分析数据层
│   ├── 01-投资概念/              # 投资和经营概念卡片
│   ├── 02-Stop-Doing-List/       # 不为清单条目
│   ├── 03-企业与品牌/            # 企业案例
│   └── 04-关键人物/              # 人物关系
│
├── site/                         # 静态网站源码与生成产物
│   ├── build.py                  # 站点生成脚本
│   ├── style.css                 # 全站样式
│   ├── search.js                 # 站内搜索
│   ├── graph.js                  # 关系索引
│   ├── assets/                   # Logo、favicon 等静态资源
│   ├── concept/ company/ person/ # 生成页面
│   ├── stop-doing/ sources/      # 生成页面
│   └── data/                     # 前端数据
│
├── gen_concepts.py               # 早期概念生成辅助脚本
└── 2025-雪球-方三文对话段永平.md  # 待补资料占位
```

## 当前网站特性

- 首页按日期稳定轮换“今日段永平”。
- 思想年表按阶段组织关键事件、概念和案例。
- 概念页包含年度频次图、演变轨迹、原话摘录和关联阅读。
- 企业页包含案例时间线、验证概念、关键原话、资料来源和外部资料。
- Stop Doing List 已按投资、经营、认知等维度结构化展示。
- 来源页支持站内引用、原文外链按钮和结构化正文呈现。
- 知识图谱已改为可搜索、可筛选的一跳关系索引。
- 引用尽量站内化，避免暴露本地路径、Markdown 文件名和工程痕迹。

## 本地运行

需要 Python 3，构建脚本依赖 `PyYAML`。

```bash
pip install pyyaml
```

重新生成分析数据：

```bash
python3 duanyongping-kb/00-analysis/scripts/build_analysis.py
```

重新生成静态网站：

```bash
python3 site/build.py
```

启动本地静态服务：

```bash
python3 -m http.server 8001 --directory site
```

然后访问：

```text
http://127.0.0.1:8001/
```

如果 `8001` 已被占用，可以换成其他端口。

## 数据层说明

`duanyongping-kb/00-analysis/` 是介于原始资料和最终页面之间的分析层：

- `events.yaml`：主年表事件，用于首页和思想年表。
- `concept-evolution.yaml`：概念演变底稿，用于概念页。
- `quote-selections.yaml`：精选语录池，用于首页和概念页。
- `company-case-timeline.yaml`：企业案例时间线。
- `concept-frequency.json`：逐年概念频次。
- `timeline-index.json`：年表聚合索引。
- `narrative-outline.md`：叙事页面草案。
- `data-methodology.md`：数据生成方法和局限。
- `validation-report.md`：覆盖率和异常检查。

YAML 文件偏人工策展，JSON 文件偏脚本生成。修改数据时，优先维护 YAML 和 Markdown，再重新构建站点。

## 来源与引用原则

本项目优先保留可追溯来源：

- 一手来源优先于二手整理。
- 可阅读原文优先于描述性出处。
- 对无法结构化的出处，只作为“出处说明”，不伪装成可点击来源。
- 外部链接集中放在资料来源、人物页、企业页和知识图谱，不在正文中泛滥。
- 概念频次仅作研究线索，不代表严格语义统计。

继续补资料时，建议只新增独立候选文件，不直接改动现有页面和构建逻辑。例如：

```text
research-output/new-sources.yaml
research-output/coverage-gaps.yaml
research-output/verification-notes.md
```

## 维护建议

新增资料的推荐流程：

1. 把原始资料放入 `duanyongping/` 的合适目录。
2. 在 `duanyongping-kb/` 中补充或修订对应概念、企业、人物、Stop Doing List 卡片。
3. 如涉及首页、年表、案例时间线或精选语录，更新 `duanyongping-kb/00-analysis/` 下的 YAML。
4. 运行分析脚本和站点构建脚本。
5. 检查关键页面和引用跳转。

构建前建议检查：

```bash
python3 -m py_compile site/build.py
python3 -m py_compile duanyongping-kb/00-analysis/scripts/build_analysis.py
node --check site/graph.js
```

## 已知局限

- 部分雪球和网易博客资料来自整理稿，仍需继续校验原始 URL、发布时间和上下文。
- 部分年份来自路径或上下文推断，不应视为严格考据结论。
- 概念频次采用关键词和别名匹配，可能受短词歧义影响。
- 企业案例中的财务、市场和持仓信息需要继续用年报、投资者关系材料或权威报道补强。
- 当前静态站点没有后端，搜索和图谱均为前端静态数据驱动。

## 免责声明

本项目基于公开资料整理，仅用于学习、研究和资料索引。内容不构成投资建议，也不代表段永平本人或相关公司的立场。引用资料版权归原作者、原发布平台或相关权利方所有。

