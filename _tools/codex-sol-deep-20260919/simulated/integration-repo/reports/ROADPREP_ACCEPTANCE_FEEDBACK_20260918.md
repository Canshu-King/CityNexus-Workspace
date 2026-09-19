# RoadPrep 派单方法论反馈

日期：2026-09-18
观察者：Qoder（第三方，未参与派单与执行）
对象：CityNexus RoadPrep 任务包（下载目录 2026-09-15 至 09-18 共 19 个）
目的：记录一个反复出现的执行侧失效模式，供派单方调整验收标准写法

---

## 一、结论摘要

派单方的指令质量明显高于执行侧的落实质量。任务包已经把正确的
验收判据写进去了，但**执行侧的 harness 能用"形式上通过"的方式
满足它**，导致真 bug 在绿灯下存活。

本文件的核心建议只有一条：

> 所有 ID 级断言，除报告结果外，必须同时报告
> **判据表达式**与**该判据为何不是恒真**。

---

## 二、证据：同一条验收标准的形式通过

### 2.1 派单方已写明的要求

`docs/REPLAN_IDENTITY_ACCEPTANCE.md` 的断言清单：

```
1. affected mutable entity is actually removed/replaced according to contract.
2. same closed Place cannot reappear through a new Activity ID.
5. UI summary matches exact diff.
6. if target resolution is uncertain, system asks/blocks instead of guessing.
```

第 2 条即"同一闭店 Place 不得通过新 Activity ID 复现"。方向完全正确。

### 2.2 执行侧的实现

`_v1922_work/run_final_v2.cjs` 第 347 行（修复前）：

```js
const closedPlaceStillPresent = postActs.some(
  (a) => (a.place_id ?? null) === targetPlace,
);
```

`targetPlace` 取自 `target.place_id ?? null`。而 `GET /journeys/{id}/experience`
返回的 activity **没有顶层 `place_id` 字段**，实测字段为：

```
id, sequence_no, type, title, start_at, end_at, locked, protected, metadata
```

因此 `targetPlace === null` 恒成立，表达式退化为"是否存在任何
`place_id` 为 null 的 activity"。实测该 journey 14/14 全部为 null，
**断言恒真**。追踪报告写 `closedPlaceReappeared=true`，形式上"通过"了
第 2 条，实际什么也没验证。

### 2.3 真 bug 恰好藏在这个盲区里

同一份 journey（`aa17d2b7-a199-4466-ad11-8ed9092782fe`）的真实数据：

| | activity | place_id | provider | 坐标 |
|---|---|---|---|---|
| v4 base seq2 | `7f284b17` | `e1ced246-…` | citynexus-v9-domain | 24.4581979, 118.0689473 |
| v5 active seq2 | `c5ca0c06` | `real-place-07e7689756fa…` | overpass | 24.4581979, 118.0689473 |

`e1ced246` 的 `external_id` 为 `CN-XIAMEN:real-place-07e7689756fa27109a8bff96`，
**直接指向 v5 使用的那条 overpass 记录**。坐标完全相同，名称同为
"OSM restaurant"。

即：被闭店的场所被"替换"成了它自己的另一条记录，diff 显示
`removed=[e1ced246…] added=[real-place-07e7689756fa…]`，方案看起来已恢复，
旅客仍被送往闭店场所。

根因 `app/replanning/mock_replan_engine.py:157`（修复前）：

```python
if place_id in occupied_place_ids or place_id == str(affected_place.id):
    continue
```

排除仅用 id 相等。domain wrapper 与 provider row 是不同 id、同一物理地点。

### 2.4 后果

三份 proposal 同时创建，`decided_at` 完全相同（18:44:51.606487）：

| proposal | 目标 | utility | 结果 |
|---|---|---|---|
| `4c3fa44c` | v5 同地点假替换 | 0.67 | **ACCEPTED** |
| `8df191fa` | v6 `real-place-1564f860`（必胜客） | 0.70 | INVALIDATED |
| `695b9529` | v7 `real-place-4717d938` | 0.70 | INVALIDATED |

作废机制本身正确（接受一个即作废其余）。问题在**排序**：假替换被排到
第一，UI 接受了第一张卡。**系统选中了唯一没真正解决问题的方案，而验收
标准第 2 条因判据恒真未能拦下它。**

---

## 三、这是一个复发模式，不是孤例

同一族错误在本项目内至少出现三次：

| 位置 | 表达式 | 失效方式 |
|---|---|---|
| `main.py` R1-a | `affected_activity_id in {row.activity_id}` | `None in {None}` → 恒真，误判受保护 |
| `run_final_v2.cjs:347` | `(a.place_id ?? null) === targetPlace` | `null === null` → 恒真 |
| `mock_replan_engine.py:157` | `place_id == str(affected_place.id)` | id 相等代替物理身份 → 恒假 |

三者共同点：**用字面表示（null / id 字符串）代替语义身份**。

值得注意：R1-a 与 harness 那处是**同一族错误的两个实例**，前者被派单方
发现并要求修复，后者由执行侧自己写出且未被察觉。这说明执行侧在修一类
错误时，没有把该错误模式回检到自己的验证代码上。

### 3.1 第四处：时区字符串比较

执行侧的子代理在 cycle4 中自查出：

> The "locked preserved = false" is my own comparison bug: the timestamps are
> the SAME instants, just rendered with different offsets (+00:00 vs +08:00).

`2026-11-06T06:00:00+00:00` 与 `2026-11-06T14:00:00+08:00` 是同一时刻，
字符串比较判为不等。同一族错误的第四个实例。

---

## 四、建议

### 4.1 验收标准层（派单方）

**建议 A：要求断言自证非恒真。**
每条 ID 级断言除结果外，须报告：
- 判据表达式原文；
- 判据两端在本次运行中的实际取值；
- 若任一端为 null/空集，必须显式说明该断言的语义。

**建议 B：禁止 `?? null` 兜底参与身份比较。**
身份字段缺失时应报 `UNKNOWN`，而非退化为 null 再参与比较。
缺失本身就是需要报告的观测结果。

**建议 C：要求交叉引用证据。**
凡涉及"实体是否被移除/替换"的断言，须同时给出被移除实体与新增实体的
**外部标识**（`provider_key`、`external_id`、坐标），而不只是内部 id。
内部 id 在跨命名空间时无判别力。

**建议 D：把"恒真/恒假判据"列为独立验收项。**
可要求执行侧提交一份"判据自查表"，逐条说明每个断言在什么情况下
会失去判别力。

### 4.2 执行侧（可在派单包中要求）

**建议 E：错误模式回检。**
修复某一类比较错误后，须在同一变更内检索自己的验证代码是否存在
同族错误。R1-a 修复时就应触发对 harness 的回检。

**建议 F：断言旁标注判据来源。**
执行侧后来自行加入的 `closed_place_reappeared_checked_via:
"metadata.semantic_key"` 是正确方向，建议推广为强制字段。

### 4.3 一个可直接加入验收矩阵的 gate

| ID | Gate | Required result |
|---|---|---|
| X01 | 判据非退化 | 每条 ID 级断言的判据两端均非 null/空集；若为 null 须显式标注 UNKNOWN 并说明语义 |
| X02 | 身份跨命名空间 | 涉及实体增删的断言须提供 external_id 或坐标级证据 |
| X03 | 同族错误回检 | 比较类修复须附一份对验证代码的同族错误检索结果 |

---

## 五、附：本次观察的边界

- 本文件基于对 `_v1922_work/` 与 `D:\moodle\CityNexus` 的只读分析，
  未参与派单、未参与执行。
- 引用的修复前代码状态取自 2026-09-18 03:30 之前的文件快照。
  执行侧已于 03:32 提交 `is_same_physical_venue()` 修复，
  新增 `test_hotfix_v2_closure_truth.py` 三个 R1-d 用例，
  全量回归 762 passed / 0 failed。
- 该修复由执行侧在收到外部结论后完成，**并非其自查发现**。
  这本身也支持第 3 节"缺少错误模式回检"的判断。

### 数据来源

- 数据库：`D:/moodle/_v1922_work/fc_evidence/_db/live.db`
- Journey：`aa17d2b7-a199-4466-ad11-8ed9092782fe`
- 追踪产物：`_v1922_work/o2_evidence/VISIBLE_UI_TRACE_XIAOMI_FINAL.json`、
  `REPLAN_IDENTITY_TRACE.json`
- 任务包：`CityNexus-EAC-Xiaomi-Trial-Final-Hotfix-v2-RoadPrep-20260918.zip`、
  `CityNexus-V19.2.4-FinalTruth-Closure-RoadPrep-20260915.zip`
