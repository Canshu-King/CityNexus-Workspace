# CityNexus Visio Phase 1 — RC2 External Review

请审查本包中的 `CityNexus_Visio_Model_Baseline_v1.0.1_RC2.vsdx` 及三个 SVG 导出。

## Expected pages

页面必须且只能是：

1. `00_Style_Guide`
2. `P1_UC_Overview`
3. `P1_Domain_Overview`

不得生成或要求生成 Part 2 页面。

## Expected semantic counts

| Page | Semantic shapes | Connectors |
|---|---:|---:|
| 00_Style_Guide | 6 | 3 |
| P1_UC_Overview | 17 | 21 |
| P1_Domain_Overview | 11 | 14 |

## Review checklist

- 是否使用 Visio 原生 UML Actor、Use Case、Subsystem、Class Master；
- Connector 是否使用原生 Association、Extend、Dependency、Composition；
- 每条 Connector 两端是否 Glue 到实际 Shape；
- Traveler 是否连接 UC-02、04、05、06、07、08、10、11、12，且不连接 UC-09；
- P1_UC_Overview 是否恰好有三条 `<<extend>>`：UC-07→UC-06、UC-09→UC-08、UC-10→UC-09；
- 外部 Actor 是否位于 CityNexus Boundary 外部；
- Domain Overview 是否显示 `<<projects from>>` 和 multiplicity；
- 是否存在 Shape overlap、Connector 穿过无关 Shape 或严重交叉；
- SVG 是否正常打开并保持可读；
- `.vsdx` 是否真正可编辑而非图片伪装。

机器验证摘要见 `phase1-render-report-v1.0.1-RC2.json`。
