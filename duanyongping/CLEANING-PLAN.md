# 段永平资料库 — 清洗方案

> 分析时间：2026-04-29  
> 分析范围：6 个 Git 仓库 + 12 篇网页文章 + 2 本 PDF

---

## 一、数据全景

| 来源 | 文件数 | 大小 | 内容类型 |
|------|--------|------|----------|
| **duan-main** | 672 | 119 MB | ⭐ 最全合集：公司里程碑、访谈、雪球问答录、网易博客（含33张高清PNG截图） |
| **duanyongping-netease** | 563 | 4.7 MB | 网易博客纯文本存档（与 duan-main 第四部分重叠但风格不同） |
| **flyinthesky-duanyongping** | 2,986 | 58 MB | 🌐 **完整 Web 应用** + 雪球按月归档（121篇） + 2,600+ 缓存JSON |
| **fastisslow** | 16 | 31 MB | PDF 合集（投资逻辑篇/商业逻辑篇/斯坦福/早期报纸） |
| **flowersprite-duanyongping** | 52 | 0.6 MB | 2010年博客片段（已含在 duan-main 中） |
| **duan-yongping-skill** | 15 | 53 KB | AI Skill 蒸馏框架（非原始资料） |
| **articles/** | 19 | ~0.8 MB | 网页存档（8篇有效 + 2篇付费墙垃圾） |
| **pdfs/** | 2 | 8.7 MB | 两个核心 PDF |
| **空目录** | 4 | 0 | business-philosophy, interviews, investment-philosophy, xueqiu-posts |

---

## 二、问题清单

### 🗑️ P0 — 必须删除

| # | 文件/目录 | 原因 | 节省空间 |
|---|-----------|------|----------|
| 1 | `business-philosophy/` `interviews/` `investment-philosophy/` `xueqiu-posts/` | 4个空目录 | — |
| 2 | `huxiu_three_win.*` `huxiu_idk.*` | 虎嗅付费墙拦截，实际内容488字节（反爬虫JS） | 22 KB |
| 3 | `zhihu_stanford_notes.html` | 403 错误页，650字节 | 1 KB |
| 4 | `duan-main/.obsidian/` | Obsidian 工作区配置文件（不是内容） | ~1 MB |
| 5 | 全仓库共22个 **小于200字节** 的占位/空文件 | 无实质内容（如 `2001年《读者》11月刊.md` 111B 只有标题） | ~3 KB |
| 6 | `fastisslow/` 中与 `pdfs/` 重复的 PDF | `段永平投资问答录(投资逻辑篇).pdf` (17MB) + `段永平投资问答录(商业逻辑篇).pdf` (3.9MB) + `在斯坦福对话段永平*.pdf` (3份不同格式) | ~22 MB |

**P0 合计可节省**：~23 MB + 消除大量噪音

### ⚠️ P1 — 需要处理

| # | 文件/目录 | 问题 | 建议 |
|---|-----------|------|------|
| 7 | `flyinthesky-duanyongping/` **除 `@大道无形我有型/` 之外的全部** | 这是完整的 Flask Web App：pipeline/、cache/ (2,600 JSON)、deploy/、static/、templates/、app.py…… | **提取雪球归档 `@大道无形我有型/`（121篇）**，删除其余 |
| 8 | `flowersprite-duanyongping/` 全部 | 52个文件，只是2010年博客的不完整片段，内容已全部包含在 duan-main 中 | **删除整个仓库** |
| 9 | `fastisslow/` 中 **非段永平原创** 的 PDF | `张昕帆：一次非常精彩的演讲.pdf` 与段永平无关 | 删除或移至 `references/` |
| 10 | `articles/` 的 `.txt` 文件 | HTML 已有，TXT 提取质量差（无格式化） | 保留 HTML，删除 TXT |

**P1 合计可节省**：~55 MB

### 📋 P2 — 建议优化

| # | 文件/目录 | 问题 | 建议 |
|---|-----------|------|------|
| 11 | `duan-main/` 中 **233个第三方内容** | 巴菲特致股东信全文、芒格演讲、马云专访、林书豪新闻、梁文冲高尔夫…… | 移到 `references/third-party/` 子目录，不与段永平原帖混淆 |
| 12 | `duan-main/` 中 **33张PNG截图** (43MB) | 大部分是雪球页面截图备份，重复于已提取为 .md 的文本内容 | 移到 `references/screenshots/` |
| 13 | `duan-main/` 的 Obsidian 内部链接 | 很多 `[[wikilink]]` 指向不存在的文件 | 保留原始格式（作为原样存档），不做修复 |
| 14 | `fastisslow/` 保留部分 | `早期报纸上的段永平.pdf`（唯一来源）、`段永平的投资逻辑(雪球).pdf`、`段永平连答49问.pdf` | 移到 `pdfs/period-articles/` |
| 15 | `duan-yongping-skill/` | 不是原始资料，是 AI Skill。但内容精炼，参考价值高 | 移到 `references/ai-skill/` |

### ✅ P3 — 直接保留（无需清洗）

| 来源 | 内容 | 保留原因 |
|------|------|----------|
| **duan-main** (清理后) | 公司里程碑、访谈、雪球问答录、网易博客 | 最完整一手/二手资料 |
| **duanyongping-netease** | 网易博客纯文本 | 与 duan-main 互补（不同整理风格） |
| **flyinthesky 的 `@大道无形我有型/`** | 雪球帖子按月归档 | 唯一按时间线整理的雪球发言 |
| **pdfs/ 两本问答录** | 投资逻辑篇 + 商业逻辑篇 | 最系统的投资哲学整理 |
| **8篇有效网页文章** | 搜狐/人民文摘/新浪/界面/中国发展简报/学术桥 | 独立来源的深度报道 |

---

## 三、清洗后目标结构

```
duanyongping/
├── README.md
│
├── 01-core/                          ← ⭐ 核心资料（优先阅读）
│   ├── duan-main/                    ← 公司里程碑 + 访谈 + 雪球问答 + 网易博客
│   └── xueqiu-timeline/             ← 从 flyinthesky 提取的雪球按月归档 (121篇)
│
├── 02-supplement/                    ← 补充资料
│   ├── netease-blog/                ← duanyongping-netease 博客存档（互补视角）
│   └── web-articles/                ← 网页文章（HTML格式，8篇有效）
│
├── 03-pdfs/                          ← PDF 文档
│   ├── 段永平投资问答录-投资逻辑篇.pdf
│   ├── 段永平投资问答录-商业逻辑篇.pdf
│   ├── period-articles/             ← 早期报纸/杂志扫描
│   │   ├── 早期报纸上的段永平.pdf
│   │   └── 段永平的投资逻辑(雪球).pdf
│   └── interviews/                  ← 访谈转录
│       └── 段永平连答49问.pdf
│
└── 99-references/                    ← 参考资料
    ├── third-party/                  ← 巴菲特/芒格/马云等引用原文
    ├── screenshots/                  ← 雪球截图备份
    ├── ai-skill/                     ← duan-yongping-skill
    └── source-index.md               ← 所有原始来源 URL 清单
```

---

## 四、统计对比

| 指标 | 清洗前 | 清洗后 | 变化 |
|------|--------|--------|------|
| 总文件数 | 4,310 | ~1,400 | -68% |
| 总大小 | 372 MB | ~250 MB | -33% |
| 空目录 | 4 | 0 | ✅ |
| 垃圾文件 | 24 (付费墙/403/占位) | 0 | ✅ |
| 重复PDF | 4份 | 0 | ✅ |
| 第三方内容 | 233 散落各处 | 归类到 references/ | ✅ |
| 技术杂物 | 2,700+ (app/缓存) | 0 | ✅ |

---

## 五、执行确认

以上方案分为三档：

- **P0 必须删**：4个空目录、4个垃圾文章、22个空文件、4份重复PDF、.obsidian/ 配置  
- **P1 建议删**：flyinthesky 应用层（保留雪球归档）、flowersprite 整仓、fastisslow 非段永平PDF、文章TXT副本
- **P2 建议移**：第三方内容归类、截图归类、fastisslow 保留 PDF 移至 pdfs/、skill 移至 references/

**是否按此方案执行？** 我建议从 P0 + P1 开始，P2 可以根据你的偏好调整。
