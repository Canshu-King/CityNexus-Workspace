# CityNexus Visio Phase 1 — v1.0.2 RC3 External Review

请审查本包中的 `CityNexus_Visio_Model_Baseline_v1.0.2_RC3.vsdx` 和三个 SVG。

本包只包含 Phase 1 三页：`00_Style_Guide`、`P1_UC_Overview`、`P1_Domain_Overview`，不得生成 Part 2。

预期语义数量：Style Guide 6 shapes / 3 connectors；Use Case 17 / 21；Domain 11 / 14。

请重点检查：

- 所有语义 Shape 的 YAML 几何位置和尺寸；
- 每个语义 Shape 是否存在 `Prop.SpecId`；
- 原生 UML Master 和 Glue endpoint；
- 专用直角路由、crossings、connector-through-shape；
- Domain 中 Activity–Place 与 Activity–CityService 的双端 multiplicity；
- 页面标题、副标题、statusTag、legend；
- SVG 中 Segoe UI/Aptos、#F8FAFC 和 CityNexus 调色板；
- `.vsdx` 是否真正可编辑。

机器检查结果见 `phase1-render-report-v1.0.2-RC3.json`。当前报告明确为 FAIL，未验证项目不得视为通过。
