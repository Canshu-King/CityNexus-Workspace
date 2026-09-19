> **SUPERSEDED (v4)** — 本文是 v2 历史叙述。T1 身份判定在 v3 已引入近坐标 AMBIGUOUS 排除（~60m），并以 `QODER_V4_IMPLEMENTATION_REPORT.md` + `V4_STATUS.md` 为准；下文若与之冲突，以 v4 报告为准。

# PHYSICAL_IDENTITY_RESULTS — v2（B2）

## v1 遗留问题（GPT 复审）
`is_same_physical_venue` 实际返回 `compare_physical_venue(...) != DIFFERENT`，把 **AMBIGUOUS 也算 True**，却把"我不确定是不是同一个"伪装成"是同一个"；且跨 provider 同实体（overpass:node 与 foursquare:place，同名同坐标同类别、仅 provider 不同）被 Rule 3 直接判 DIFFERENT —— 但不同 provider object ≠ 不同物理地点。wrapper 正则 `^[A-Z][A-Z0-9_-]*:` 过宽，任意大写前缀会被当 CityNexus 交叉引用。

## v2 改动（`mock_replan_engine.py`）
1. **身份真值与排除策略解耦**：
   - `compare_physical_venue()` → SAME / DIFFERENT / AMBIGUOUS
   - `is_same_physical_venue()` → **仅 SAME** 为 True（诚实身份）
   - `should_exclude_replacement_candidate()` → SAME 或 AMBIGUOUS 都 True（fail-safe 排除）
   `rank_closure_replacements` 的排除点改用 `should_exclude_replacement_candidate`。
2. **跨 provider 不武断判异**：两侧 provider-scoped 元组都存在但不等时，若 `_corroborated_same_venue`（坐标相等 + 归一名相等 + 类别不冲突）成立 → **AMBIGUOUS**（据排除策略 fail-safe 排除），否则才 DIFFERENT。
3. **wrapper 正则收紧**：只认 CityNexus 文档形式 `^CN-[A-Z0-9]+:...`，任意 `FOO:bar` 不再被当交叉引用。

## 回归（unit 20 passed，含 4 条 v2 新回归）
- 跨 provider 同实体 → AMBIGUOUS（is_same False、excluded True）
- 同 namespace 不同对象且无互证 → DIFFERENT
- 任意大写 external_id 不作 wrapper（identity.wrapper_reference None）
- 跨 provider alias 的已关闭场馆被排除出替换族（rank 不再重推它）
保留 v1：null/空 id、坐标-only、node/123 vs way/123、不同 provider 同数字、provider-scoped 相同+漂移、显式 wrapper→provider 行 SAME。
