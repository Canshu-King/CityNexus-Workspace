# CityNexus 项目交接报告

更新时间：2026-09-06  
项目根目录：`D:\moodle\CityNexus`  
当前主题：P1 Use Case 路由候选的 Contact Gate 修复

## 1. 背景与当前阶段

CityNexus 是软件工程课程项目，正式母体选题为 **Smart City Traveler System（智慧城市旅行者系统，第 11 题）**。产品方向是自适应城市旅程编排平台（Adaptive Urban Journey Orchestration Platform）。

领域模型、需求基线、用例规格和 Visio 语义规格已经建立；C1–C4 以及 C4E1 校准阶段已经完成外部冻结。当前仅处于 Visio 正式渲染前的 P1 路由规划与几何质量门阶段。

## 2. 冻结状态与保护边界

外部审核确认：

- C1 = `FROZEN_PASS`
- C2 = `FROZEN_PASS`
- C3 = `FROZEN_PASS`
- C4 = `FROZEN_PASS`
- C4E1 / Extend calibration = 已接受并冻结
- RC6 = `BLOCKED`，等待 P1 路由候选通过 Contact Gate

禁止修改：`domain-model\`、`requirements\`、`use-cases\`、`visio-spec\pages\p1_uc_overview.yaml`，以及全部 C1–C4/C4.1/C4.1a/C4.1b/C4.1c/C4.1d/C4E1 历史校准文件。

禁止执行：生成 RC6、正式 Phase 1 Visio、P1 Domain、Part 2，搜索新的 GitHub Visio 工具，或修改 validator 来掩盖失败。

本阶段允许编辑的唯一语义候选文件：

`D:\moodle\CityNexus\visio-renderer\phase1-routing-rc6-candidate.yaml`

## 3. 最近应用的补丁

补丁来源：`C:\Users\仓鼠王\Downloads\CityNexus-P1-Route-Contact-Gate-and-CodexWeb-Prep-Patch.zip`

已合并文件：

- `visio-renderer\calibration\audit_p1_route_contacts.py`
- `visio-renderer\calibration\validate_p1_route_candidate_v2.py`
- `visio-renderer\tests\test_p1_route_contact_gate_contract.py`

审阅过的说明：`AUDIT-RESULT.md`、`P1-ROUTE-REPAIR-CODEX-EXECUTION.md`、`CODEX-CHATGPT-WEB-CITYNEXUS-GUIDE.md`。

## 4. 当前候选文件

文件：`D:\moodle\CityNexus\visio-renderer\phase1-routing-rc6-candidate.yaml`

已恢复为原始 Review Package 的字节级版本。SHA-256：

`8C1661EBB1A9D5A371F48EF800316DD643F391BEEC559EB2A4B8065EED75182D`

metadata 状态仍为 `PLANNING_REQUIRED`；21 条路线均有显式 waypoint。

以下 3 条 Extend 路线必须保持原样，并保持 `FROZEN_FROM_C4E1`：

```yaml
EXT-07-06: [[17.2, 6.6], [8.3, 6.6], [8.3, 9.7], [11.1, 9.7]]
EXT-09-08: [[17.2, 10.2], [7.5, 10.2], [7.5, 13.4], [11.1, 13.4]]
EXT-10-09: [[23.3, 9.4], [27.0, 9.4], [27.0, 14.2], [17.2, 14.2]]
```

优先只重规划其余 18 条 Association 路线。

## 5. 最新验证结果

执行命令：

```powershell
cd D:\moodle\CityNexus\visio-renderer
python .\calibration\validate_p1_route_candidate_v2.py
```

旧基础几何门通过：`semanticConnectorCount=21`、`candidateRouteCount=21`、`explicitGeometryRouteCount=21`、`properCrossingCount=0`、`collinearOverlapPairCount=0`。

新的 hardened Contact Gate 失败：

- `contactPairCount = 46`
- `uniqueContactCount = 55`
- `tjunction = 22`
- `shared_endpoint = 33`
- `shortSegmentCount = 9`
- `redundantCollinearPointCount = 88`
- crossing / overlap 仍为 0
- v2 状态：`FAIL`

失败原因：旧 validator 只统计真正的内部 crossing，没有拦截路线端点接触另一条路线内部、不同路线共享中间 waypoint 等视觉假连接。

报告文件：

- `visio-renderer\calibration\out\P1_UC_ROUTE_CANDIDATE-report.json`
- `visio-renderer\calibration\out\P1_UC_ROUTE_CANDIDATE-v2-report.json`
- `visio-renderer\calibration\out\P1_UC_ROUTE_CONTACT-AUDIT.json`

## 6. 静态测试结果

执行：

```powershell
cd D:\moodle\CityNexus\visio-renderer
python -m pytest .\tests -q
```

结果：`47 passed, 1 failed`。

唯一失败为 `tests/test_p1_rc6_route_prep_contract.py::test_only_three_extend_routes_are_frozen`。旧测试仍假设只有 3 条路线有 waypoint、其余 18 条为 `null`；当前候选已为 21 条路线提供显式几何。因此这是过时测试契约造成的 false negative，不是 Contact Gate 通过。当前任务不要修改该旧测试，也不要为让 pytest 变绿而修改语义规则。

## 7. 外部 Review Package

路径：`D:\moodle\CityNexus\review\CityNexus-P1-Route-Contact-Gate-Review-Package-v0.2.zip`

SHA-256：`3394C9094ECA623184E775FBCA3029E9BA062224C435DC3338C723E2E69C00AC`

包内含候选 YAML、路由几何模块、Contact audit、v1/v2 validator、报告、静态测试说明、P1 语义页面参考、执行合同和 manifest；已检查无 `__pycache__` 与 `*.pyc`。

## 8. 下一窗口的标准操作

先检查工作区：

```powershell
cd D:\moodle\CityNexus
git status --short
```

阅读报告：

```powershell
Get-Content .\visio-renderer\calibration\out\P1_UC_ROUTE_CANDIDATE-v2-report.json
Get-Content .\visio-renderer\calibration\out\P1_UC_ROUTE_CONTACT-AUDIT.json
```

运行测试和 v2 gate：

```powershell
cd D:\moodle\CityNexus\visio-renderer
python -m pytest .\tests -q
python .\calibration\validate_p1_route_candidate_v2.py
```

以 `P1_UC_ROUTE_CONTACT-AUDIT.json` 为精确修复清单，只编辑 `phase1-routing-rc6-candidate.yaml`。每次修改后重跑 v2 validator。

## 9. 最终路由质量门

必须同时达到：

- `semanticConnectorCount = 21`
- `candidateRouteCount = 21`
- `explicitGeometryRouteCount = 21`
- `properCrossingCount = 0`
- `collinearOverlapPairCount = 0`
- `contactPairCount = 0`
- `uniqueContactCount = 0`
- `tjunction = 0`
- `shared_endpoint = 0`
- `shortSegmentCount = 0`
- `redundantCollinearPointCount = 0`

并继续满足：正交、endpoint tangent 正确、不穿越 unrelated node、全部在页面边界内、无 0.02/0.03/0.05 cm micro-jog、尽量少 bends。

Contact Gate 将路线视为闭合线段集合；端点落到另一条路线中间、路线共享中间点、短线段、冗余共线点都算失败。

## 10. 成功条件与硬停止

只有 v2 validator 返回 `status = PASS` 且失败数为 0，才可以将 metadata.status 改为 `GEOMETRY_PASS_PENDING_EXTERNAL_FREEZE`，将 18 条 Association 的 planningStatus 改为 `ROUTE_PLANNED_PENDING_EXTERNAL_FREEZE`，并保持 3 条 Extend 为 `FROZEN_FROM_C4E1`。随后立即停止，重新打包交 GPT 外部审核。

无论成功与否，都不要渲染 Visio、生成 RC6、生成 P1 Domain 或开始 Part 2。无法达到零 Contact 时必须如实报告 FAIL，不要修改 validator、删除历史实验或创建新的 C4.x 版本。

## 11. Git 注意事项

仓库包含大量历史未跟踪文件和实验文件；本路由任务没有自动 commit。不要执行 `git add .` 或未获授权的提交。后续提交只能包含用户明确批准的文件。

可能存在的历史实验临时文件（不要误加入提交/Review Package）：`visio-renderer\_keep.yaml`、`visio-renderer\candidate-original.yaml`、`visio-renderer\orig.save.yaml`、`visio-renderer\phase1-routing-test.yaml`。

## 12. 可直接复制给新窗口的首条消息

```text
你是 CityNexus 接手窗口。先阅读 D:\\moodle\\CityNexus\\HANDOFF-ROUTE-CONTACT-GATE.md。

当前状态：C1/C2/C3/C4 = FROZEN_PASS；RC6 = BLOCKED。最新 P1 路由候选的旧 crossing/overlap gate 通过，但 hardened Contact Gate 失败：contactPairCount=46、uniqueContactCount=55、tjunction=22、shared_endpoint=33、shortSegmentCount=9、redundantCollinearPointCount=88。不要生成 Visio、RC6 或 Part 2。

先运行：
cd D:\\moodle\\CityNexus
git status --short
cd visio-renderer
python -m pytest .\\tests -q
python .\\calibration\\validate_p1_route_candidate_v2.py

只允许修改 visio-renderer\\phase1-routing-rc6-candidate.yaml；不得修改 domain-model、requirements、use-cases、visio-spec 或历史 C4 校准。3 条 Extend 路线 EXT-07-06、EXT-09-08、EXT-10-09 必须保持 FROZEN_FROM_C4E1。以 P1_UC_ROUTE_CONTACT-AUDIT.json 为修复清单。只有 v2 validator 返回 PASS 且所有接触、短线段、冗余共线点均为 0，才把状态改为待外部冻结并停止打包；否则如实报告 FAIL。
```
