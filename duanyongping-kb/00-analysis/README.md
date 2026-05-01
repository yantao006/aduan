# 段永平思想时间轴数据层

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
