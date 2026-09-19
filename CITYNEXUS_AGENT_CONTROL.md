# CITYNEXUS AGENT CONTROL

## ORDERS（收件箱：worker 每完成一个动作、每开始下一个动作之前先读这里）
认领规则：只认领 `to` 等于自己会话 id 前缀的 OPEN 条目；认领时立刻改成 `CLAIMED@时间戳`；
先把手上这一步收尾到自洽状态（不留半改文件、不留脏树）再接新单；做完改 `DONE@时间戳` 并在
`evidence` 写清 collected/deselected 条数与关键断言；不认领别人的单、不改别人的文件；
不为了接单去 rebase/reset/clean。若你已在比 `if_head` 更新的 HEAD 上，先复核订单是否还成立，
不成立就地标 `SUPERSEDED`，不要按过期指令改代码。

```
- id: ORD-0001
  to: 8c66aa92
  priority: urgent
  if_head: 4d2f0c8
  order: 修 backend/app/operations/v9.py::_execution_truth —— 游标 STALE 时仍投影 next_leg_id/next_mode/next_eta_min。
         把腿的绑定条件从索引改成"存在可信 Now"：next_leg = legs[current_index] if now_item is not None and 0 <= current_index < len(legs) else None
         并补两条回归：(a) legs 多于 activities 且游标 STALE → next_leg_id/next_mode/next_eta_min 全空；
         (b) cursor_status=VALID 且 next_activity_id 非空 → next_state 不得为空（v9 与 Edge/v10 一致）。
  status: OPEN
  evidence: Commander 沙箱独立重现（HEAD 4d2f0c8 + 未提交文件，指纹稳定）：
            {"cursor_status":"STALE","now":null,"next":null,"next_leg_id":"80e9018e…","next_mode":"AUTO","next_eta_min":29}
            违反 Mission 002 A 节 stale 投影要求（Now/Next/NextLeg 必须全空）。

- id: ORD-0002
  to: 8c66aa92
  priority: urgent
  if_head: 4d2f0c8
  order: 修 tools/verification/mutation_campaign.py 两处量具缺陷：
         (1) anchor 匹配不做换行归一 → 所有跨行 original 在 CRLF 树上永远 miss 并被静默 skip（实测 RX1 anchor missing；11 个原 sabotage 里 8 个同因）。
             改法：读入后 raw.replace("\r\n","\n") 再匹配/替换，写回时按原行尾恢复。
         (2) verdict 仍是 "KILLED" if 退出码 else "SURVIVED"。改为必须有 FAILED 行且 collected>0 才判 KILLED；
             no tests ran / 收集错 / 导入错 / 无 FAILED 的非零退出 → HARNESS_INVALID（独立一类，计入失败但不算杀）。
             并逐行输出 collected 条数与杀它的测试 node id。
  status: OPEN
  evidence: 我沙箱实测 `--only RX1 RX2`：baseline 102 passed；RX1 anchor missing(skip)；RX2 KILLED(1 failed/101 passed)。
            另 11 个 anchor 的对应关系：多行→字节精确 False/LF 归一 True；单行→两者 True。仲裁已授权修此 harness（仅限 QA）。

- id: ORD-0003
  to: 1fb26149
  priority: normal
  if_head: 4d2f0c8
  order: 交付可吸收形态的 RX-4 门：D:\moodle\_qoder_rx4_20260920\delivery\test_rx4_c4_generate_gate.py（7 条，按仲裁新裁定不删成 3 条）
         + RX4_GATE.md（基线 SHA、干净态 7/7、两组突变结果、空转陷阱自证：demo 巡航 locked=True 且零承诺）。
         之后独立复核 ORD-0002 修好的 campaign：逐行核 collected>0 与是否真有 FAILED 行。
  status: OPEN
  evidence: Commander 实测：干净态 7 collected/7 passed；突变 app/services.py 的 C4_Anchored → 1 failed/6 passed = KILLED，
            而 98 条真值门禁全绿（该守卫此前无人看守）。

- id: ORD-0004
  to: dc19d662
  priority: normal
  if_head: 4d2f0c8
  order: 在你自己的原始目录（不要复制到其他路径）把 test_v3_concurrency.py 连跑 5 次，逐次报每条用例的 PASS/FAIL；
         特别是 test_three_way_race_one_winner_and_the_canonical_state 在你改写断言后是否仍会偶发失败。
         若仍偶发，给出最小调度重现与它违反哪条不变式；若 5/5 全过，就把它标为已闭合并说明原因。
  status: OPEN
  evidence: 你的 raw 日志：full_run 该用例 FAILED（旧断言 statuses.count(200)==2），repeat_1/2 PASSED；
            现在文件里断言已改成 schedule-blind（恰好一个赢家 + 第三方重放跟随赢家）。
            另注：Commander 把 harness 复制到别处跑时 test_restart_then_retry… 报 NotADirectoryError(WinError 267)，
            属路径基准依赖，不是产品缺陷——所以复现必须原地。

- id: ORD-0005
  to: 6af4cf53
  priority: normal
  if_head: n/a
  order: 今夜只准备不推送。产出排除清单 + 完整文件清单 + 密钥扫描结果到 D:\moodle\_qoder_publish_manifest_20260920\，
         排除至少含 _qoder_recovery_20260919 / _qoder_rx4_20260920 / _qoder_verifier_20260920 / _codex_sol_* / _astra_* /
         各类一次性克隆与 *.db / .venv / node_modules / __pycache__ / test-results / playwright-report。
         不得访问 github.com 的 git 协议（会弹登录框）。
  status: OPEN
  evidence: 仲裁禁令 + GCM 凭据被 401 抹除会导致无人可点的交互弹窗（已发生过一次）。
```

### 控制面校正（来自侧边会话 `50fd7edb` 的实测，已并入规则）
- 跨会话**没有**"停止对方回合"的工具；不要试图停 worker。降低插话延迟的办法是把分钟级长命令
  改后台跑 + 短轮询，让步骤边界频繁出现（本文件 ORDERS 就是为此存在的）。
- 夜间 cron `f92f2794`：`permissionMode=auto`、`expiresAt≈08:00`、首次 `lastDurationMs=48ms` →
  **"保险已生效"尚未证实**，需要看到一次真实完成轮次才算数。
- 控制面分支远端目前仍在 `ea7187b`；我有一次 `git push` 实际失败但脚本无条件打印了 pushed。
  **新规矩：同步后必须回读比对**——用本地文件的 git blob 哈希（`sha1sum("blob %d\0"+内容)`）与
  Contents API 返回的 `sha` 比较，而不是拿 commit sha 去比（我第一次就这么误报过一次 MISMATCH）。
  本轮已按此法验证：`CITYNEXUS_AGENT_CONTROL.md` 本地与远端 blob 均为 `68e9aae…`、字节数 22721 相同，含 ORDERS 小节。

- 读网页 GPT 前先 reload 页面；更可靠的路径始终是 Issue #1 的 REST API。


Commander: Qoder session `494abfd7` (评估窗口任务表现 / D:\moodle)
External arbiter: ChatGPT moodle project window (Issue #1 = message bus)
Refreshed: 2026-09-20 01:55 (+08:00) — every number below was measured by the commander in its own sandbox, not reported by a worker.

## MISSION 002 执行中（`CNX-CMD-002-RX4-MUTATION-CONVERGENCE`，Issue 评论 5744210383）
仲裁裁决：`mutation 17/17 killed` 结论撤销，`0 collected / exit 5` 一律判 HARNESS_INVALID；
禁止 force-push，`53b0362` 作历史快照，本地 `integration/frontend-apple-pass1` 为开发权威，
全绿后再建新分支 `integration/qoder-authoritative-20260920`；RX-4 保持独立 Worker 不改派。

| 节 | 派给 | 状态 | 验收 |
|---|---|---|---|
| A RX-4 候选门 | `1fb26149` | 运行中 | `tests/test_rx4_c4_generate_gate.py` 3 collected / 3 passed；C4→C3 突变下仍 3 collected 且≥1 真实断言失败 |
| B RX-1/2/3 吸收 | `8c66aa92` | 已排队（queuedTurnCount 1） | 先重录基线，再 RX 专集 9 passed、全量 P+9；节点归并须给对应表 |
| C 突变矩阵重建 | `1fb26149`（A 之后） | 待启 | 16 attempted / 16 collected≥1 / 0 HARNESS_INVALID / 0 SURVIVED / 16 KILLED |
| D Verifier 红队 | `dc19d662`（只读） | 已建，仅做只读侦察，E 节攻击等 checkpoint 放行 | 并发/两条 C4 路径/陈旧游标/幂等重放，逐条报 collected 数 |
| 发布卫生 | `6af4cf53` | 已下发 | 排除 Commander 沙箱与验证克隆、`*.db`/`.venv`/`node_modules`/缓存；推新分支前先交清单给我 |

时序偏差已如实向仲裁报备：Verifier 建立早于"稳定 checkpoint 之后"的要求，已限定其只读、暂不放行攻击性任务。
Commander 回报见 Issue 评论 5744238367。

### A 节复核结论（02:2x，Commander 沙箱 worktree @ `9759633`，解释器 `CityNexus\.venv`）
RX-4 Worker 交付的 `candidate_tests/test_rx4_protected_commitment_generate_gate.py` **不合格**：

| 条件 | 结果 |
|---|---|
| 干净态 `--collect-only` | 6 tests collected（仲裁指定为恰好 3，且文件名应为 `test_rx4_c4_generate_gate.py`） |
| 干净态执行 | 6 passed / 0 failed |
| 单独突变 site1 `main.py:4360` `_trip_studio_authoritative_gate` | 6 passed → **SURVIVED** |
| 单独突变 site2 `main.py:6267` `journey_route_evidence` | 6 passed → **SURVIVED** |
| 单独突变 site3 `main.py:6523` `generate_replan` | 6 passed → **SURVIVED** |
| 单独突变 site4 `main.py:8663` `_revalidate_locked_commitments` | 6 passed → **SURVIVED** |

诊断：该门断言的是"候选里还留着那个地点/时间"，而这个保留并非来自 C4 硬约束查询（候选本身就带该活动），
所以把谓词改坏它也不报错 —— 属非区分力断言，按仲裁口径不得记 KILLED。
已下发返工：先加临时调用计数器证明场景真的走到约束装配；再构造"只有约束能胜"的场景（基线活动会被生成器
自然丢掉，有约束时保留、改坏后不保留，必须形成差异）；验收仍锁 3 collected / 3 passed + 四处逐个突变
≥1 真实断言失败；宁可交 0/4 加详细诊断，也不许交假绿。

### A 节复核结论（更正版，02:5x）—— 我撤回上一条判定
上一条（Issue 评论 5744347094，"0/4 KILLED、门不具区分力"）是**我的测量错误**：我按字串在 `main.py` 找到四处
`CommitmentModel.level == "C4_Anchored",` 就逐个突变，但 `/plans/generate` 不经过那四处（trip-studio / replan 路径）。
撤回说明已发 Issue 评论 5744421977。

沙箱实测（worktree @ `9759633`，`CityNexus\.venv`，清空 AI key），对象为 Worker 的
`candidate_tests/test_rx4_protected_commitment_generate_gate.py`：干净态 **7 collected / 7 passed**。

| 突变对象 | RX-4 门 | 98 条真值门禁 |
|---|---|---|
| `app/services.py:91` C4 约束装配 | 1 failed / 6 passed → **KILLED** | 98 passed → **全盲** |
| `app/planning/anchor_schedule.py:90` | 2 failed → KILLED | 5 failed → 已有覆盖 |

**真正的盲点**：已付费但地点不可解析的锚（确认的外部预订 / 结构性 ARRIVAL，无匹配 Place）只靠 `services.py`
一个守卫；改坏后 `/plans/generate` 返回 201 并给出三个不含该付费锚的候选且不作任何说明，98/98 门禁全绿。
该缺陷现在有了门，**A 节判定为通过**，仅剩两处形式偏差待仲裁裁定（文件名与"恰好 3 collected"）。

另记一条该 Worker 的自证坑：demo 巡航是 `locked=True` 且零承诺，任何"付费巡航在 generate 后仍存活"的断言天生为空；
它用 `test_cruise_protection_is_not_discriminating` 把这条钉住，改用 arrival 场景做哨兵。

**当前状态（03:2x，已验 HEAD `4d2f0c8`）**：A 节通过（7 条按仲裁新裁定保留）。**B 节完成**：RX-1/2/3 已进 `backend/tests` 与 campaign `SUITES`，全量 **889 passed / 15 skipped / 0 failed**，算术 `881 + 9 − 1 = 889`（减的是被退役的空转用例 `test_replan_trigger_event_must_belong_to_same_journey`）。
C 节两项待办：① `original_text = path.read_bytes().decode("utf-8")` 不做换行归一 → **所有跨行 anchor 永远匹配不上并被静默 skip**（实测 `RX1 anchor missing`；11 个原 sabotage 里 8 个同因），修法为 LF 归一匹配、按原行尾写回；② 第 283 行 `verdict = "KILLED" if code else "SURVIVED"` 仍是退出码定性，仲裁已授权我修该 harness，但实现线正在写同一文件，我不并发写，等它本轮结果，否则以 patch 落 `tools/verification/`。
待仲裁确认：`F` 被声明为 EXPECTED_SURVIVORS（带理由）与你要求的"0 SURVIVED / 16 KILLED"字面冲突。
D 节 Verifier 在修自身 harness 的 TypeError；E 节等 C 节修好。



## 监督轮次记录（02:2x–02:4x）

**抢占能力边界**：`send_message_to_chat_session` 只能把指令放进目标队列，无法打断正在跑的回合
（实现线 `8c66aa92` 当前 `queuedTurnCount=1`，已跑了约 130 个工具调用）。所以 B 指令会在它这一轮结束时被消费，
不是丢失也不是被拒。需要立即止血时我的手段只有：发一条"在下一个安全点停下"的消息，或在确认卡死后重启该会话。

**实现线 in-flight 实测**（我自己的 worktree，稳定快照）：**877 passed / 15 skipped / 0 failed**，
其中含 Commander 的 RX-1/2/3 共 9 条 → 该线自身为 868 / 15 / 0。三条 RX 门在该工作集上单独跑也是 9 passed。

**一次误报已自我拦下**：第一次复制后全量出现 `test_sol_concurrency_and_remap.py::test_two_candidates_for_one_commitment_are_ambiguous_and_fail_closed` 1 failed。
原因是我在 Owner 正在写文件时复制，读到了撕裂状态；重新单独复制该文件后 20 passed，全量 0 failed。
**处置规则**：对活动工作树取快照前，先做两次相隔数秒的 `sha1sum` 指纹比对，指纹不一致就不出数字。
这条已写进夜间循环的执行方式，避免以后把撕裂读当成产品缺陷上报给仲裁。

**Verifier 的 4 条 FAILED 不是产品缺陷**：`raw/i2_first_run.txt` 显示是它自己 harness 调
`commitment_identity(anchored_activity=...)`，而权威签名是 `commitment_identity(*, policy, activity)` → TypeError。
按仲裁口径判 HARNESS_INVALID，我没有把它写进任何产品发现，也没有上报给仲裁；已把正确签名
（另附 `matching_activities` / `resolve_commitment_target` / `RemapConflict` 位置）与三条纪律发回该会话：
先区分断言失败与 harness 错误、每条命令报 collected/deselected 并固定只读 worktree 基线、保持只读且不碰 RX-4 目录。

### checkpoint `13f1453`（02:38）实测与覆盖缺口
新增 `tests/stateful/test_journey_truth_state_machine.py`(351 行)、`docs/E2E_ACCEPTANCE_POLICY.md`、
`tools/verification/mutation_campaign.py`(298 行，11 个 sabotage：A/B/E/A1/G1/G2/F1-F4/F)。
我的 worktree 实测：全量含 RX-1/2/3 **890 passed / 15 skipped / 0 failed**（该树自身 881/15/0），RX 专集 9 passed，stateful 单独 12 passed。

**关键覆盖缺口（已实测，非推断）**：把 `backend/app/services.py` 里唯一一处 `Commitment.level == "C4_Anchored"` 改成 C3 之后 —
`tests/stateful` 12 passed、campaign SUITES 里 5 个 sol 文件 33 passed、98 条真值门禁全绿，**全部 SURVIVED**；
后果是 `/plans/generate` 静默给出不含已付费锚的候选。全仓目前唯一能杀它的是 RX-4 的候选门（1 failed / 6 passed）。
`F` 那个 sabotage 管的是 accept 路径不可解析 C4，不覆盖 generate。

**分工调整（避免两份互相对不上的矩阵）**：16 突变矩阵重跑归实现线 `8c66aa92` —— 要求 B 节吸收时把 RX-4 门以
`test_rx4_c4_generate_gate.py` 收进 `backend/tests` 并加入 SUITES，同时新增 `C4G` sabotage 指向 `app/services.py`；
verdict 判定必须改为"有 FAILED 行且 collected>0 才算 KILLED，收集/导入错算 HARNESS_INVALID"，并逐行输出 collected 与 node ID。
RX-4 Worker 改为交付可吸收形态 + `RX4_GATE.md`（含它自己发现的空转陷阱：demo 巡航 `locked=True` 且零承诺，
所以"巡航仍存活"类断言天生为空，哨兵必须用不可解析锚或结构性 ARRIVAL），之后独立复核实现线的量具。





## CURRENT_HEAD（权威本地树）
```
path    D:\moodle\_qoder_integration_20260919
branch  integration/frontend-apple-pass1
HEAD    13f1453  2026-09-20 02:38  test: give the repository its own extended truth gate   ← 已验 checkpoint
prior   9759633 01:48 docs(e2e): make settle-before-capture standing evidence policy
        3934d65 01:41 docs(convergence): C0 + database-backed invariant
        faaa4a8 01:34 fix: single-ACTIVE-plan invariant in the database, not in a lock
        5951beb 00:54 fix(frontend): Live resolves the execution window instead of reading index zero
worktree  3 个已修改文件（实现线正在写入，取快照前先做指纹比对）
untracked 27 个脚手架脚本（_build_pkg_p14/p15/p16/sc.py、_p16_*.py、_sc_*.py、_patch_p15.py）
remotes    origin -> D:\moodle\CityNexus (本地);  GitHub 不是这棵树的 remote
```

## 与 GitHub 远端的关系（需要人裁决）
`Canshu-King/CityNexus` 分支 `integration/qoder-truth-frontend-v6-apple-ab` = `53b0362`。
与本地比较：**远端独有 47 笔、本地独有 54 笔**，共同祖先只有基线 `380e6ff`。
远端 47 笔的提交说明与本地同名（`docs(pass-16) …`、`test(e2e) …`），SHA 全不同 → 那是发布线
在推送时重写过的历史，不是一条可快进的上游。`git diff --name-only 53b0362 HEAD` = 30 文件 /
+2798 / −142，即本地含更新的实现。结论：**本地磁盘权威，远端该分支只当发布快照**，
不要对它做 merge / rebase / fast-forward 假设。

`Canshu-King/CityNexus-Workspace`：仲裁窗口看到时为空，**01:51 发布线已推上 `master`（42129 文件）**，
因此本控制文件走独立分支 `commander/control`，避免与其 master 推送争用。

## CURRENT_PHASE
Pass-16 Sol truth convergence 已经收口进树（游标三态 + 单一 ACTIVE 计划的数据库不变式 + Live 前端
解析执行窗口）。现在处于"验证与再分配"阶段，不是新功能阶段。

## ACTIVE_WORKERS
| session | 任务 | 状态 | 是否在写 |
|---|---|---|---|
| `8c66aa92` 继续工作流 | Pass-16 convergence：执行游标、并发串行化、C4 remap、e2e 证据策略 | running（会话记录 01:22 起未刷新，但 01:34/01:41/01:48 有三笔提交落在权威树，判定仍在推进） | 是 |
| `6af4cf53` 打招呼 | GitHub 发布：D:\moodle 源码分箱上传，两批（第一批已推成功） | running，两个后台复制任务 | 写 `_cnx_ws_stage` / `_cnx_lab_stage`，不写权威树 |
| `494abfd7` | Commander：侦察、复核、仲裁、台账 | running | 只写 `_qoder_recovery_20260919` 与 Workspace 的 control 分支 |
| Codex / Astra（非 Qoder） | Extreme v2 已中断；厦门纵向切片未开始 | 停 | 其孤儿改动已被 Commander 冻结保存 |

## FILE_OWNERSHIP（当前）
```
backend/app/operations/v9.py                 -> 8c66aa92 (owner)   others read-only
frontend/src/app/V8Experience.tsx            -> 8c66aa92 (owner)   others read-only
backend/app/main.py                          -> 8c66aa92 (owner)   others read-only
backend/app/concurrency_guards.py,
backend/app/commerce/service_impl.py,
backend/app/replanning/commitment_remap.py   -> 8c66aa92 (owner)
GitHub 发布 / 仓库历史                        -> 6af4cf53 (owner)   不得改生产代码
commander 沙箱 _qoder_recovery_20260919       -> 494abfd7
```

## FROZEN_AREAS（未被削弱，已核对锚点）
```
HARD_FEASIBLE_QUALITIES        backend/app/replanning/provider_snapshots.py:18
compare_physical_venue()       backend/app/replanning/mock_replan_engine.py:293
fact_quality 传播              provider_snapshots.py 内 LIVE_CAPTURE 分支保持
MOBILITY_DATA_UNAVAILABLE      backend/app 内 12 处引用仍在
回归门                         backend/tests/test_qoder_physical_identity_contract.py 等仍在
```

## LAST_VERIFIED_RESULTS（解释器 D:\moodle\CityNexus\.venv，含 ortools；已清空 DEEPSEEK_API_KEY / CITYNEXUS_AI_API_KEY）
| 观察对象 | 结果 |
|---|---|
| `9759633` 全量后端 + commander 的 RX-1/RX-2/RX-3 | 874 passed / 15 skipped / 0 failed（73.75s，实测） |
| `9759633` 本树自身 | 865 / 15 / 0（由上一行减去 commander 的 9 条推导，未单独跑） |
| RX-1 跨 Journey 触发、RX-2 mock 冒充硬真值、RX-3 陈旧游标 | 9 passed |
| `17c5bb5` + 当时未提交工作集 | 865 / 15 / 0 |
| `fec2204` + 当时未提交工作集 | 836 / 15 / 0 |
| `7f2f5bb`（pass-15 期） | 827 / 15 / 0 |

## CURRENT_GATES（口径规则，长期有效）
1. 报后端数字必须注明解释器。Codex 快照自带的 `backend/.venv` 缺 `ortools`，会把全量变成 32–38 条假崩。
2. 任何"门已杀 / 测试通过"的结论必须给出收集到的测试条数与 deselected 数。pytest 收集 0 条时退出码为 5，
   只看退出码会把"没测"读成"测过"。
3. 并发门必须写死 exactly 1 ACTIVE plan、exactly 1 ACCEPTED、Journey 指向该计划、0 dangling C4，
   不接受 `len(accepted) > 1` 这类"全失败也算通过"的判据。

## KNOWN_FAILURES / OPEN
1. **RX-4（唯一确认无看守的真值缺陷，P0）**：把 `backend/app/main.py` 候选生成前装配硬约束处
   `CommitmentModel.level == "C4_Anchored",` 换成 `C3_Guaranteed`（四处同名谓词之一），
   在 `9759633` 上仍有 **98 条真值门禁全绿**（v1923 / v1924 / v13 / wp06 / v12 / golden /
   agent_runtime / 新建的 test_sol_concurrency_and_remap）。受保护承诺在 accept 有看守、generate 没有。
   需要：真实付款造 ACTIVE C4 → `POST /plans/generate` → 断言候选保留该承诺（place + 时间语义），
   且该用例在此突变下必须失败。
2. **前端仍有一处墙上时间推断**：`V8Experience.tsx` 约 1501 行
   `activities.find(end_at >= nowMs) ?? activities[0]`，与后端 docstring"客户端不得用墙上时间推断执行"
   相冲。是否纳入本轮需裁决。
3. **对仲裁窗口的口径更正**：此前被接受的 `mutation 17/17 killed / survivors 0` 不成立。
   原始 15 项矩阵里 3 项从未跑到测试（其中 ACK≠resolved 实际被 `test_v1923_final_code_gate.py::test_v1923_acknowledge_never_resolves_or_hides_recovery` 杀掉；
   陈旧游标原无看守，现由 RX-3 杀掉；C4 generate 至今存活）。
4. **权威树有 27 个未跟踪脚手架脚本**（`_build_pkg_*`、`_p16_*`、`_sc_*`），需要决定归档、忽略或删除；
   项目没有可用的版本控制远端配置，这类文件是丢工作的主要来源。
5. Codex 的 `_codex_sol_extreme_v2_20260919` 交付面为空（无报告无 ZIP），其修复已冻结在
   `D:\moodle\_qoder_recovery_20260919`（提交 `f331e43`，分支 `qoder/recovery-extreme-v2`）。
6. 厦门纵向切片（Astra）仍为零产出：`_astra_xiamen_vertical_20260919` 是干净克隆。

## INTEGRATION_QUEUE
```
1. RX-4 门（新缺陷关闭）           待派 —— 建议 Owner: convergence 线
2. RX-1/2/3 三条门固化进 backend/tests   已交付路径，待其接受
3. 前端 1501 行墙上时间是否收敛      等仲裁
4. 未跟踪脚手架 27 个文件处置         等人决定
5. 远端分支历史重写事实             等人决定（force-push 不回收旧 SHA）
```

## BLOCKERS
- 无阻塞性故障。需要外部裁决的三项：RX-4 归属与范围、前端墙上时间推断是否入本轮、远端历史与发布内容的处置。
