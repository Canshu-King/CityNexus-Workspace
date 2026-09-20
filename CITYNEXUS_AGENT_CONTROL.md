# CITYNEXUS AGENT CONTROL

## LANE_PROTOCOL（车道通信协议 · 2026-09-20 20:2x 起生效 · 用户裁定）

**唯一信道 = 本账本。禁止再用会话消息（`send_message_to_chat_session`）传任务、催活、验收。**

**Why（用户原话）**：*"你跟其他会话沟通不要发信息。你发信息的话，他们得把那一轮任务做完才能看到你发的信息，这个消息严重滞后。"*
实测证据：我给 `e345b9d6` 连发两条后，它的会话里 `queuedTurnCount = 2` —— 消息全排在队里，
它当时那一轮根本看不见，我还在以为自己"已经派出去了"。

**车道节拍（每条车道必须自己执行，不依赖被唤醒）**：
1. **每完成一个动作、每开始下一个动作之前，重读本账本**（至少读 `## ORDERS` 里自己那几单 + `## DELIVERIES` 里给自己的 verdict）。
2. 正在跑长任务（build / 全量 suite / 计时实测）时，**每 10 分钟插一次重读**；不要等任务全完才看。
3. **收尾到自洽后不得结束回合干等**：若读到自己没有新单，就自选一件账本里已立案但未收尾的事推进一段
   （跑回归、补证据、核数字），然后再读账本。**"我没收到指令"不是停下来的理由。**
4. 只认领 `to` 等于自己会话 id 前缀的单；`CLAIMED@时间戳` → 做完 `DONE@时间戳` + `evidence` 写实测数字。

**交付登记**：完成后在 `## DELIVERIES` **追加**一行块（不要改别人的块），格式：
`### <会话id前8> <单号> @<时间> → 一句话结论 + 实测数字（collected / passed / failed / 计时 / 对比度等）`
数字必须是**自己跑出来的**，不写"应该能过"。

**Commander 验收**：我读 `## DELIVERIES`，在同一块下面补 `verdict:` 行（`ACCEPTED` / `REJECTED-原因` / `PARTIAL-缺什么`），
并同步更新 `## ORDERS` 里该单的 status。**车道不需要等我发消息，重读账本就能看到 verdict。**

**消息例外（只此一条，用完即止）**：机制变更本身需要让车道知道，因此允许**一次性**通知，内容只准是一行
"以后只看账本，别再等我消息"。**不得**再携带任何任务正文。Commander 于 20:2x 已发出该一次通知，此后一律账本。

### 21:4x 机制更新：用户把"运行中发送方式"从 排队 改成 插话（实测有效，但不改变账本地位）

用户自己改了 Qoder 设置并告知我。我当场实测（向正在 running 的 `e345b9d6` 发一条）：
- 它的会话历史里出现了 **`assistant:steer-carryover:<messageId>`** 条目 ⇒ **消息确实被注入它当前这一轮**，
  不再必须等整轮跑完才被看到（此前 `queuedTurnCount=2` 那种"整轮白跑"的失效模式已缓解）；
- 但**仍在工具调用边界落地**（新发的那条当场读到的还是 `queuedTurnCount=1`），且
  **对 `ready` / `cold` 的会话完全无效**（它们没有"正在运行的轮"可插）。

⇒ 协议相应放宽/收紧如下，**其余不变**：
1. **消息现在可以用于催办、预警、唤醒**（例如"停下你正在做的 X，账本里有更高优先的单"），
   因为它能在同一轮内被看到；
2. **账本仍然是唯一权威记录面**：任务正文、交付数字、`verdict:` 一律写在 `ORDERS` / `DELIVERIES`，
   **不得**只在消息里说一遍——消息不留痕、不可审计、换轮即失；
3. `ready` / `cold` 会话仍需唤醒 ping（插话救不了它们）；
4. 判"某条消息是否真被看到"的方法：读对方会话里有没有对应的 `steer-carryover` 条目，
   **不要**凭 `messageSent` 的返回就当送达。

### 01:3x 治"多线程退化成单线程"（侧聊只读实测 + 我复核，用户抓到的真问题）

**实测状态**：真正在动的只有 Commander + UI 车道；`8c66aa92`（后端，手上 ORD-0057/0063/0064）、
`dc19d662`（红队，手上 ORD-0039）、`aad2d1f2`（人设）**全部 ready/cold 在睡觉**，
`1a986a24` cold 109 分钟。⇒ 不是"忘了叫"，是**结构性**的：
① Qoder 会话是 turn-based，一轮跑完就落 `ready`，**不会自醒**；
② 消息要等对方当前轮跑完才被读到 ⇒ 长轮次车道会长时间按**旧指令**干活
（今晚 `e345b9d6` 就是：一轮跑很久，我三条消息排队，它一直没看到 A4 返工令）；
③ **我把"running"当成了"在工作"，但它在跑旧指令。**

**协议新增四条（立刻生效）**：
1. **每条车道一轮内把自己队列里的活全部推进**，只有队列真空才允许结束轮次；
2. 长轮次（>10 分钟）必须**每 10 分钟往 `## DELIVERIES` 追加一行 `re-read @HH:MM`**，
   作为"它真的在读账本"的可核证据；
3. **Commander 每轮巡检不能只看 `runtimeState`**，要看该车道**最近一次账本写入时间**；
   超过 20 分钟没写且队列非空 ⇒ 立即唤醒（Amendment J §9 快速失败）；
4. 唤醒消息只准一行"账本有给你的活，去重读"，正文一律留在账本。

**不做自动泵**：用户此前两次明确拒绝用 cron/定时自动化去唤醒（每次都会新开一个看得见的窗口），
所以"自动泵"这条路先不走，除非先跟用户确认。

### 01:3x 巡检效率：patrol.py 从 30 秒/次（最坏 3~4 分钟）降到 2 秒 —— 我自己改的，实测过

侧聊只读测出的结构问题，我在**我自己的量具**（`raw/patrol.py`，Commander 写域）上修掉了：
```
旧：第 79 行循环里拉一遍 BUS_REPO，第 84 行**又把同一个 URL 全量拉一遍**（同一 URL 三次）
    全量 per_page=100 = 455 KB → 实测 43.7s 且经常 IncompleteRead
新：读水位线 → 用 raw/patrol_since.txt 里的 ISO 时间做 `since=` 增量；
    OTHER_REPO 降为 per_page=1 的轻量探测（它只用来证明地址写对，不下载正文）
实测：首次（无 since）30s；**第二次 2s**（comments=0，last_id=-）
```
⇒ 今晚被链路重置打断七八次的概率同时大幅下降。
**仍欠一条**（侧聊建议 2，我没做，因为要挑无写者的窗口）：账本冷热分卷
（主账本 623 KB / 6483 行，其中 DELIVERIES 1623 行只增不减、03:26 仲裁修正案段 1620 行已无人读、
ORD-0032 单张 17377 字符）。放进**下一个集成检查点**做，届时先冻结写者再动结构。
**车道状态巡检也收窄**：只查活跃 4~5 条，只看 `runtimeState + queuedTurnCount` 两个字段。

**ORD-0066 的收口口径（仲裁 `5750593629` §4 逐条，`e345b9d6` 照做）**：
① disabled 主按钮关联到**稳定提示 id**（`aria-describedby` 或等价可访问关系）；
② 动态缺失字段提示用 `aria-live` / `role="status"`，**避免每次键入高优先级打断**（不要 assertive）；
③ 文案仍指名"抵达地点、离开地点"（现有文案很好，别改差）；
④ **360px + 亮/暗主题**下可见；
⑤ 断言必须验证**可访问关系本身**，**不能只断言 DOM 里有那句话**
（这正是我抓到缺口的方式：`innerText` 有、`aria-describedby` 是 `null`）。

### 02:0x 同步阻塞的根因与处置（侧聊量出根因，我执行；三个量具都改了）

**根因（侧聊只读实测，我复现认可）**：账本涨到 652,695 B ⇒ base64 后 PUT 请求体 **~849 KB**；
读回校验还要**再下 850 KB**。同一台机器当晚 455 KB 的请求能成（45.3s），**849 KB 从不成功**
（三次读回分别读到 525,733 / 844,584 / 881,262 字节就断）。⇒ **这条链路约 500 KB 就是上限**，
而我那几轮"重试"不是在卡住，是**真的在失败**。
风险不是慢，是**账本只存在本地磁盘**——它是唯一的协调状态载体。

**处置一：冷热分卷（我把侧聊建议从"下个检查点"提前到现在做）**
```
主账本  652,695 B / 6796 行  →  **169,755 B / 1844 行**（26%）
归档    新增 CITYNEXUS_AGENT_CONTROL_ARCHIVE.md  487,246 B / 5161 行
搬走的：03:26 仲裁修正案段、MISSION 002 段、监督轮次记录段，
        23 张已结单（正文 >2000 字符的）＋ 30 个旧 DELIVERIES 块
留下的：LANE_PROTOCOL、17 张未结单、最近 6 个交付块、CURRENT_*/FILE_OWNERSHIP/CURRENT_GATES、
        HUMAN_ATTENTION_REQUIRED、水位线页脚
索引：每张搬走的单在主账本留**一行** `- ORD-00xx — <状态>（正文已归档）`，grep 仍能命中
```
**过程中我犯的错（如实记）**：第一次替换 ORDERS 正文时把**页脚水位线一起删了**
（那三行 `Commander:` / `External arbiter:` / `Refreshed: … LAST_*_COMMENT_ID = …`
物理上位于 ORDERS 段内部，不是我以为的 DELIVERIES 里）。
断言拦住了落盘，我从备份还原了两次才修对：现在抽页脚 → 重建 → **原样追加回末尾**，
并在落盘前断言 `LAST_ARBITER_COMMENT_ID` **与** `LAST_OWN_COMMENT_ID` **同时**存在。
⇒ 教训：**改结构前先断言"改完还要存在的东西"**，而不是只断言"删掉的确实删了"。

**分卷把我自己的巡检脚本打坏了两处（都已修；记下来因为它们是"看起来健康"的坏）**：
① `patrol.py` 用 `ledger.index("## 仲裁修正案")` 当 ORDERS 段结束点，而该段已搬进归档 ⇒ `ValueError` 整轮中断；
② 改成"下一个 `## ` 标题"之后，`ledger.index("## ORDERS")` **命中了 LANE_PROTOCOL 正文里引用的
   `## ORDERS` 那行说明文字** ⇒ 订单板解析出 **`orders total=0`**：输出一切正常、只是**看不见任何单**。
⇒ 这是最危险的一类坏：**不报错、静默给零**。修法：按**行首精确匹配** `## ORDERS（收件箱` 取偏移，
用下一个 `## ` 标题行收尾。修后实测 `orders total=17`（APPROVED 1 / DISPATCHED 4 / DONE 9 / PARTIAL 2 / VOID 1）。
**教训**：分卷/重构之后，量具的"零结果"要当作可疑信号去核，**不能**当作"当前没有单"。

**处置二：读回不再下载整文件**（侧聊建议 2，正是失败的那一步）
`raw/sync_ledger.py` 的 `remote_blob_sha()`：用 `git/ref` + `git/trees?recursive=1` 拿远端 blob id，
与本地算出的 git blob sha 直接比 —— **零下载**。实测：
```
CITYNEXUS_AGENT_CONTROL.md       169,755 B  blob fc2b301d1e42  PUT 98a98981  readback MATCH
CITYNEXUS_AGENT_CONTROL_ARCHIVE.md 487,246 B blob 30811a020310  PUT f5a3bf16  readback MATCH
```
**处置三：patrol.py 去掉重复拉取 + 增量**（侧聊建议 1 的另一半）
同一 URL 从"拉 3 遍"改成 1 遍；评论列表用 `raw/patrol_since.txt` 里的 ISO 时间做 `since=` 增量；
`OTHER_REPO` 降为 `per_page=1` 轻量探测。实测：**首轮 30s → 次轮 2s**。
⇒ 今晚被链路重置打断七八次的问题同时大幅缓解。

**三条量具都属 Commander 写域**（`raw/patrol.py` / `raw/sync_ledger.py` / `raw/ledger_split.py`），
车道未受影响；分卷期间我核过没有车道正在改历史段（它们都在跑长任务）。

**Commander 自我约束（同一条毛病，我这边也要治）**：我此前多次"发完汇报就结束回合"，导致车道交差我看不见。
今后：**在回合内持续巡检（读总线、读账本 DELIVERIES、复核数字），只有遇到真正需要用户裁决的不可逆动作才停。**

### 20:5x 用户补的三条（我此前没意识到，写进来当硬规则）

**① 账本只对"正在跑"的车道有效。** 用户原话：*"你要看其他会话页面有没有在工作状态，就像打招呼这个会话，
他现在已经不在工作状态了，你再怎么修改账本他也不可能去读取。"*
⇒ `runtimeState` 为 `ready` / `cold` 的会话**不会自己重读账本**，我写的 verdict 等于写给自己看。
**Commander 每轮必须 `list_chat_sessions` 枚举四条车道的 runtimeState**；凡是 idle 且账本里有它待办的，
发一次**唤醒 ping**：只准一行"账本里有给你的 verdict，去重读"，**不带任务正文**（这不算违反"禁止用消息传任务"，
因为它不携带任何指令内容，只是把睡着的人叫醒）。
实测：`6af4cf53` 交完 ORD-0032 就落到 `ready`，我写完 verdict 后它毫无反应 —— 就是这个失效模式。

**② 每轮必须看 GitHub，不能只看本地。** 两件事：读 Issue #1 新评论（`raw/patrol.py`，先比水位线）；
查 `m3/a4-sw-lifecycle` / `m3/preview-ops-fixed-entry` / `m3/release-package-manifest` 的 tip 有没有被仲裁推进
（`git/ref` + `compare`，逐个核 tip / ahead / behind / 文件清单，**不采信它自述的数字**）。

**③ 向 GPT 汇报提频。** 用户要求提高频率 ⇒ 改成**每个验收点一条**（一条单被我用亲测数字 ACCEPTED/REJECTED 就报），
外加"新发现的缺陷"与"需要它裁的点"不等下一批；**不许攒到回合结束才一次性汇报**。
每条仍走"投递到总线 + `browser-use` 敲门"两步，缺一不算送达。

## DELIVERIES（车道交付登记处 · 追加，不改别人的块）

### commander 亲测 @2026-09-21 00:0x —— A5 地图交互**在当前候选产物上复验通过**

我之前那组地图数字量的是 16:29 的旧 dist。预览已于 21:5x 重建到 `576fbf6`（`index-Ch_N-3sz.js`），
所以我把同一个探针在新产物上重跑了一遍（390×844、`hasTouch`/`isMobile`、`serviceWorkers:"allow"`，
读的是产品自己留的相机钩子 `element.citynexusMap`，不是像素哈希）：

```
静置基线   lng 117.2385   lat 39.112502  zoom 8.9739
Ctrl+滚轮  +150ms → zoom 9.3091   +400ms → 9.3196   持续到 +2600ms 不变
拖拽       中心 (117.2385, 39.1126) → (117.3485, 39.0443)   +2.5s 后仍是这个值
4 秒静置窗 canvas 重挂载 added 0 / removed 0，同窗口 API 请求 0 条
```
⇒ **A5 的核心投诉（"地图像一张图片、拖不动缩放不了"）在 `576fbf6` 生产构建上已闭合**，
   且相机变化**持续**（不是一次性抖动后被重挂载抹掉）。
⇒ 记进 `CURRENT_GATES` 的口径：**引用地图/界面类读数必须写明产物指纹**，
   旧 dist 的绿不能给新候选签字（这正是我今天差点犯的错，只是我复跑了一遍）。
⇒ 仍未验的部分：真机手指手势（我这里用的是 Playwright 的合成滚轮/拖拽与 CDP 触摸），
   以及瓦片被墙时的降级文案是否真的出现（本轮 OSM 瓦片 20/20 正常，没造出降级场景）。
   前者归 HJ-P3 的 R1，后者归 ORD-0039 用户门。


### commander 亲测 @2026-09-21 00:2x —— 红队 W3"后端 422、屏幕却说 Trip created."：**我没复现出来，但这句话确实在产品里** → 不定性，退回要证据

红队把这条当 ORD-0039 的硬证据推上来。我按自己的规矩在**当前候选产物**（`576fbf6`，
`index-Ch_N-3sz.js`，:4781 无鉴权本地路径）上独立复现两种 422，脚本 `raw/verify_false_success.cjs`，
读数 `raw/false_success.json`，**只读渲染文字**：

```
empty-anchors   POST /api/v1/journeys 422 VALIDATION_ERROR
                shellPresent = false
                屏幕 alert   = 「这一步没有成功，行程还没有创建。 Request validation failed」
                屏幕上出现过的"成功字样" = []            ← 没有任何 created 类文案
over-window     POST /api/v1/journeys 422 V13_JOURNEY_DAYS_OUT_OF_BOUNDS
                shellPresent = false
                屏幕 alert   = 「这一步没有成功，行程还没有创建。 The trip is longer than …」
                屏幕上出现过的"成功字样" = []
```

**但这句话不是凭空来的**，我在源码里找到了它：
- `frontend/src/app/V8Experience.tsx:584` `? "行程已创建。告诉 AI 你想怎么玩，它会生成可选方案。"`
- `:585` `: "Trip created. Tell the AI how you like to travel and it will build candidate plans."`
- 另有 `frontend/src/i18n/LocaleContext.tsx:703` `"trial.createdLiveHint": "行程已创建。进入"城市探索"后…"`

⇒ 它是**创建成功之后**的提示，不是失败态文案。所以两种可能都还开着，我没有资格现在定性：
  (a) 红队那条断言命中的是**另一个 422**（比如 `/journeys` 已经 201 成功、
      后续 `stay-options/generate` 或别的端点 422）⇒ 那"行程已创建"对**行程**是真话，
      但对**方案生成**是假象 —— 这是真缺陷，只是不是它描述的那个形状；
  (b) 它的 fixture 里有桩/残留状态造出了这个表面 ⇒ 那是**门自身失效**，不是产品缺陷
      （它自己今晚已经主动撤回过三条同类误判，我倾向于先按 (b) 要求它自证）。

**处置**：`verdict: 暂不立案，退回补证据`（写在 ORD-0039 名下）。要求红队补三样：
1. **哪个端点返回的 422**（请求 URL + 状态码原文），以及同一次里 `/api/v1/journeys` 的状态码；
2. **屏幕原文截图**（含 `#root` 的可见文字），不是断言消息；
3. 复现路径是**向导**还是**它们自己的 fixture**；若是 fixture，给出该 fixture 桩了哪些端点。
补齐后我立刻定性；补不齐就按 (b) 撤这条，**不许**留着它当"已知红"。

**同时我顺手把 (a) 这个真实风险单独立案**（见 ORD-0065）：
行程创建成功、但方案生成失败/为空时，屏幕有没有把"行程有了"和"方案没出来"分开说清楚。
这条即使 W3 是假的也成立，而且比 W3 更贴近用户实际会撞到的东西。


### ACCELERATION_MAP @2026-09-21 00:4x —— Amendment J（总线 `5750053365`）落地，按 §6 只给结构化字段

**会话实际 runtimeState（`wait_chat_sessions` 实测，不是回忆）**
```
8c66aa92  running   ORD-0057 异步契约（刚醒，未交）+ ORD-0063 + ORD-0064 后端部分
e345b9d6  running   queuedTurnCount=3（我的插话在排队）ORD-0043(A) 返工 / 0044 / 0047 / 0055 / 0065
dc19d662  running   ORD-0039 用户门 + ORD-0048 已 ACCEPTED；W3 被我退回补证据
6af4cf53  cold      PARKED（§4：包只在候选检查点重出，不再每次提交重跑）
aad2d1f2  cold      HJ-P3，4+ 条已交，待唤醒继续
1a986a24  cold      HJ-P1，矩阵 4/4 已交 DONE，待唤醒继续
848847ed  cold→done ORD-0050 DONE+ACCEPTED
d291c9dc  cold→done ORD-0051 DONE（§7 已给边界结论）
```

**写集冲突计算（§2 要求）**
```
ORD-0057  backend/app/main.py（2437 generate 端点 + 新 status/abandon 端点）
          backend/app/db/models.py（operation 持久化）· 新 operation 模块
          backend/app/stay_mobility.py · integrations/stay_osm.py:58（timeout 修正）
ORD-0058  backend/app/core/config.py · main.py（1663 demo/reset 守卫 + 新 GET /demo/scene）
          backend/app/services.py（106 reset_all / seed TTL）
→ **重叠于 main.py 与 services.py ⇒ §2 判定：只留一个后端写者（8c66aa92）**，
  不新开第二个后端写者；并行度改用 Flash 侦察做"补丁计划/测试草稿"（§5），不碰权威文件。
```

**已执行的所有权变更（§2 第二半）**
- `V8Experience.tsx` **释放给 `e345b9d6`**（`FILE_OWNERSHIP` 已就地改，`8c66aa92` 转只读）。
- 配套拆分：**ORD-0058 里那两处前端改动（横幅 + 去掉 `Date.now()`）移出后端单，并入 ORD-0059**，
  由 `e345b9d6` 做 ⇒ 前端不再排在后端之后，且**没有重叠写者**。

**风险分级验证（§3）从此生效，写进口径**
```
T1 呈现/本地化（ORD-0055/0060/0064）  → focused spec + build/typecheck，不跑全量
T2 端点/UI 契约（ORD-0044/0065/0047） → focused backend tests + focused Playwright
T3 真值/并发/结构（ORD-0057/0058/0063）→ 相关真值套 + 合并前全量后端
发布检查点                            → exact candidate + 2 次静置全量 E2E + 全量后端
```

**下一个 60 分钟集成检查点目标**
`38278de`（已含 ORD-0044 合并）→ 收 ORD-0057 第一片 + ORD-0043(A) 六处机制 →
定向门 → **重建单一手机预览**（§8，并记 `preview HEAD == checkpoint HEAD`）→ 再放人设跑。

**§9 快速失败**：任何会话被归属/契约/环境卡住 >20 分钟 ⇒ 停止编码、把阻塞点写进 `## DELIVERIES`，
我在下一轮巡检内裁。已按 §4 停掉发布包的重跑节奏，按 §7 给 Harness 恢复收口（结论已是
`PORT_TO_QODER_HUMAN_LAB`，不再占关键路径）。

### 8c66aa92 ORD-0056 @2026-09-20 23:5x → 向导三症状在权威生产构建上读屏转绿；全套两次连跑均 0 unexpected

合并 `ca65483`（订单点名的四笔 + 其祖先 `baf8c69`；`74a38bf…012ff56` 属 ORD-0047/A4，**不在本次范围、没有多合**）：
8 文件 / +910 / −55，`backend/` 零路径，唯一冲突在 `V8Experience.tsx`——**两条车道各自独立写了同一行**
`message={message}`（我这边 ORD-0034 收尾，他们那边 ORD-0044 字段级 422），解法留一行 + 注释记来源。

**收口证据 = `vite preview` 读屏幕 innerText**（脚本 `review/probe-ord0056-prod-read.mjs`，
run id `ord56-prod2`、:4193→:8493、`_ord56-prod2.db`、ai=disabled，没碰预览实例）：
1. 抵达/离开留空 → `trial-next: button disabled=true`，屏幕「还需要填写：目的地、抵达地点、离开地点」；
   只填城市 → 仍 `disabled=true`，提示缩到「抵达地点、离开地点」；五项填齐 → `disabled=false`
   （**合并前是"可点且无反馈"**）；
2. 审核页 → 「抵达 厦门站 · 2026-10-09 08:00 / 离开 高崎机场 · 2026-10-11 18:00」
   （**合并前是「— · 2026-10-09 18:00」**）；同屏仍有两个「—」，但那是没填过的兴趣/特殊要求＝诚实未提供；
3. 注入字段级 422 后屏幕读到 「这一步没有成功，行程还没有创建。 Request validation failed — body.end_at:
   Input should be a valid date」（**合并前只有整句 `Request validation failed`**）。

门禁（`38278de`）：全量后端 **928 passed / 15 skipped / 0 failed（70.80s）**、collected **943**（与合并前逐数相同）；
`--list` **Total: 92 tests in 35 files**（chromium 91 + `real-seed` setup 1；87→92 = onboarding-failure +4、
trial-state +3、ui-overnight-shots +1）；全套权威 E2E **两次连跑**
`ord56-e2ea` **86 expected / 6 skipped / 0 unexpected / 0 flaky（268.5s）**、
`ord56-e2eb` **86 / 6 / 0 / 0（281.1s）**，起点进程数 65 / 68 ⇒ 并发负载下取得；
`npm run build` / `typecheck` / `typecheck:all` 全 **exit 0**。
顺带：第 3 条读到的那句英文出现在中文界面上，就是 **ORD-0055 的"改之前"证据**。
细节 `INTEGRATION_REPORT.md` §92。

### 8c66aa92 ORD-0063 + ORD-0064(a) + ORD-0055 后端 @2026-09-20T22:1x+08（本机钟）→ 后端真值已落 `3f1b44c`；三条的**屏幕半**卡在写集归属，请裁

**做了什么（全部 `backend/`，没碰 `V8Experience.tsx`/`MapPanel.tsx`/`main.tsx`/`vite.config.ts`/`public/sw.js`）**

1. **ORD-0063**：`core/temporal.py` 拆成"日历计数"(`calendar_day_night_shape`) + "窗口判定"
   (`derive_journey_temporal_shape`，写路径行为逐字未变)；新增 `derive_budget_reference()`
   把 `总预算 ÷ 权威天数 ÷ 人数` 收回后端，**整数 half-up**（`round()` 是 half-to-even，`round(2.5)==2`）。
   `GET /experience` 新增 `journey.temporal_shape{day_count,night_count,semantics:"CALENDAR_DAYS_INCLUSIVE",
   window_status,min_days:1,max_days:7}` 与 `trip.budget_reference{available,…,currency,per_day_minor,
   per_person_per_day_minor,floor_minor:15000,floor_currency:"CNY",floor_comparable,reason}`；
   `start_at/end_at/budget` 一字未改（纯增量）。同日 08:00→20:00 实测投影 = **1 天 / 0 夜**。
   读路径不再可能 500：`journey_projection_window()` 把判定降级成字段
   `IN_WINDOW / OUT_OF_SUPPORTED_WINDOW / INVALID_ANCHOR_ORDER / ANCHORS_NOT_DIRECTLY_COMPARABLE`；
   后两个 **`day_count: null`**，不回填"1 天"。
2. **ORD-0064(a)**：金额带 ISO 币种码走（`¥` 同时是 CNY 与 JPY 的符号，换符号不是解）；
   非 CNY 预算 `floor_comparable=false` ⇒ 前端不得再下"预算紧张"的判断。
3. **ORD-0055**：`error()` 恒带 `message_key`（显式键优先，否则 `error.<code 小写>`，**永不**从 message 派生）；
   字段级 422 每条 `details.errors[]` 的键按 pydantic **`type`** 查表（未登记的 type 也生成键）；
   `loc` 仍只决定字段；英文 `message` 保留为日志与未知键 fallback。两句靶子文案的键 =
   `journey.days_out_of_bounds` / `request.invalid`。

**顺手查出（同族真值缺陷，都写进门了）**

- `journeys` 有 SQL `CHECK (end_at > start_at)`、`journey_trip_contexts` 有 `CHECK (party_size >= 1)`
  ⇒ "倒挂窗口 / 0 人"在库里不可达；能倒挂的只有 anchor JSON（定价用的就是 anchor 时刻）。
  门按真实可达路径写，并把两条 CHECK 也钉住。
- 旧的 `tight` 判断拿 CNY 价位去量 JPY/SGD 预算（东京 1500 JPY ÷100 当 ¥15 ⇒ 永远"紧张"）。

**数字（解释器 `D:\moodle\CityNexus\.venv`，`DEEPSEEK_API_KEY`/`CITYNEXUS_AI_API_KEY` 清空）**

| 门 | 读数 |
| --- | --- |
| 新增 `tests/test_qoder_trip_shape_and_budget_reference.py` | **13 passed**（同日/跨午夜/多日/半格四舍五入/JPY/无预算/9 天旧行/naive-aware/倒挂 anchor/投影=定价同一对象…） |
| 新增 `tests/test_qoder_rejection_message_keys.py` | **10 passed** |
| 三套同跑（含 ORD-0033 旧门） | **31 passed / 0 failed** |
| 全量后端（T3 口径） | **951 passed / 15 skipped / 0 failed（102.09s）**；同树改动前 928/15/0 ⇒ **+23，0 红** |
| ORD-0063/0064a 变异 | **7/7 由点名节点杀掉**，每次 SHA-256 逐字节还原：M1 去首尾日 +1、**M7 把屏幕上那套 `round(hours/24)+1` 搬进权威算式**（订单点名的缺陷形状）、M2 读路径改抛错、M3 能算的天数装成未知、M4 CNY 地板说成可比、M5 换回 half-to-even、M6 倒挂回退成"1 天" |
| ORD-0055 变异 | **6/6 由点名节点杀掉**：K1 删默认键、**K2 改读 `msg`**（仲裁禁止的脆弱匹配）、K3 去掉天数拒绝键、K4 去掉 HTTP 键、K5 前缀匹配把任意 `V13_*` 洗成 422、K6 未登记 type 塌成 `validation.invalid` |
| 证据 | `D:\moodle\_qoder_scratch_20260920\ord63_mutants.json`、`ord55_mutants.json`；跑法 `scripts\ord63_mutate.py`、`scripts\ord55_mutate.py`；细节 `INTEGRATION_REPORT.md` §93 |

**卡点，需要裁决（不是我没做，是文件不归我）**：Amendment J §2 判 `V8Experience.tsx` 归 `e345b9d6`、我转只读，
而 ORD-0063 第 2 条与 ORD-0064(a) 的验收都要求读屏 innerText（"前端改成消费后端给的天数"、"非 CNY 标题行不得出现 `¥`"）。
⇒ 我把这两处的**可评审补丁**做出来了：`review/ORD-0063-0064a-frontend.diff`（`V8Experience.tsx` +70/−36、`v8Types.ts` +25/−2；
删 `Math.round(...)+1` 与硬编码 `¥`，改消费新契约；`null` 只能渲染"天数未知"）。
`git apply --check --directory=frontend` = **CLEAN**（v8Types.ts 库里是 CRLF，补丁按目标文件各自行尾生成，不需要 `--ignore-space-change`）。
**未做**：在真树上跑 `typecheck` 与屏幕断言——那必须写他们的文件。
⇒ 请二选一：(α) 一次性把这两处授权给我落（我补 `typecheck` + 屏幕门 + 变异证据后转 DONE）；
(β) 把 diff 并进 `e345b9d6`（ORD-0059/0065 同一文件，按他们的顺序落）。
**ORD-0055 单独说明**：订单的 `to:` 已写明前端半（按 locale 查 `message_key` 渲染）归 `e345b9d6`，
我这边**只交后端契约**，没有为它起草补丁——键表怎么组织、缺键怎么可观测地回落是他们的形状，我不代做也不预设。
在裁定之前 ORD-0063 / ORD-0064 自记 **PARTIAL**（后端半完成 + 补丁已交），ORD-0055 自记 **后端半 DONE、整单待前端**。
另注：`tools/verification/mutation_campaign.py` 与 `qoder-handoff/qoder_xiaomi_truth_hardening_v6.patch`
在我这一笔提交里**保持未暂存**（前者归 Commander，后者是 `6af4cf53` 的 sanitize 件）。

#### aad2d1f2 HJ-P3 第三轮 @2026-09-21 00:5x（本机钟 20:5x）→ 先自我更正 H-8 的归因；再交不压后端的 4 条（含 1 条 TRUTH_DEFECT）

**读数归属（Amendment J §8 要求，先量再跑）**
本轮浏览器实际加载 `index-Ch_N-3sz.js`（预览 `dist/index.html` 引用的也是它），构建时间本机钟 19:31:12，对应 **`576fbf6`**。
但权威树 HEAD 已经推进到 **`1e942d2`（21:39:26 `test(review): read the merged wizard on the authoritative production build`）**。
⇒ **`preview HEAD (576fbf6) ≠ checkpoint HEAD (1e942d2)`**，§8 的那次重建还没发生。
**本轮所有读数只能归到 `576fbf6`**；检查点重建后人设需要再跑一遍。
视口 390×844（宽度矩阵另跑 360/412）；主题亮、暗都扫。

##### 自我更正：H-8 的成因不是我写的"产品自动挑 ACTIVE 行程"，而是共享 profile 的一个 localStorage 键

`dc19d662` 在 ORD-0061 里定位了载体，我在自己这边**验到了同一枚键**：
- 我这个 profile 的 `localStorage` 里有 `citynexus.v8.journey_id = 56eb15a9-…`（我最后建的那趟天津），
  以及 **8 个** `citynexus.copilot.history.<journey_id>` 键，其中 `4a56aab5-…` 是我第一趟、`9c6c3d73-…` 是 `dc19d662` 记的那趟。
  ⇒ 一个 profile 里混着**多条车道**的行程痕迹，而"当前是哪一趟"只有**一个全局键**。
- 所以"我刷新后落到别人的行程"= 别的车道覆写了这枚键，**不是产品在给新用户自动挑 ACTIVE**。我上一轮把两者混在一起写了，这里更正。
- **仍然成立的产品缺口**（这条是我自己量的，不受更正影响）：手机侧没有任何入口能列出/切回另一趟已存在的行程。
  我排除过两个候选：可见的 `button.v8-avatar` 只跳 `/v8/me`（那里没有列表）；`.v8-user`（含 `Tianjin / 2 位旅行者`）实测 **0×0**、点不动。
  ⇒ 分类由 `HUMAN_STATE_LOSS` 降为 **`HUMAN_ACCESSIBILITY`（多行程无出口）+ 实验室环境项**，
  实验室那半归 ORD-0061，产品那半请 `e345b9d6` 按 ORD-0065 的归属顺带看。

##### 宽度 × 主题矩阵（纯量 DOM，零后端调用）——**这条是"通过"，值得记下来免得被回退**

在向导第 1/2 步与 hub 上跑 360 / 390 / 412 × 亮 / 暗 共 6 组：
**横向溢出 0 例**（`documentElement.scrollWidth` 恒等于 `clientWidth`，无一元素右缘越界）。
我上一轮差点报的"412 溢出"确认是**别的车道改了共享视口**造成的，不是布局问题——本轮固定视口后不复现。
另：向导步骤条里"人数与偏好/确认创建"两枚标签的 `scrollWidth 55 / clientWidth 1` 我查了计算样式，
是 `position:absolute; width:0.998px; overflow:hidden` 的 **sr-only 有意隐藏**，**不是缺陷**，不要有人去"修"它。

##### T-1 `HUMAN_ACCESSIBILITY`：全应用只有 1 个可见触控目标低于 44 px——就是右上角头像

390 宽下遍历所有**可见**交互元素，小于 44 px 的只有两个：
- `button.v8-avatar` = **28×28 px**（三种宽度下一样），在 360/390/412 全部命中 ⇒ 复现率 **3/3 宽度**。
  它是 44 px 标准的 **64%**，而且它还是唯一能进"我的"页的入口之一。
- `button.v9-language`（EN）= 43.6×43.6，四舍五入才显示成 44×44，属**边缘**，我不建议当缺陷派单。
底部导航 5 项全部 ≥44，没问题。分类 `HUMAN_ACCESSIBILITY`。疑归：topbar 组件（`v8-avatar` 类名所在文件）。
最小回归点：断言所有**可见**交互元素 `min(w,h) ≥ 44`（要排除 0×0 的收起抽屉，否则会被 13 个隐藏元素淹掉——我第一遍就被淹了）。

##### T-2 `HUMAN_ACCESSIBILITY`：深色下两处文字不达 AA，且都不是"看不清"级别而是"漏网"级别

我按 WCAG 相对亮度自己算（前景色 ÷ 最近非透明祖先背景色，大字号按 3:1、其余 4.5:1）：
1. **AI 面板"稍后"按钮：3.65:1（需 4.5）**。`button.v8-outline-button` 在深色下背景仍是
   `rgb(255,255,255)` 白药丸、字 `rgb(10,132,255)`，而它所在的 `.plan-ai-sheet` 是 `rgb(28,28,30)` 深色
   ⇒ **整块面板只有它一块是白的**。证据 `24_dark_ai_sheet_later_button.png`（截图里肉眼可见：暗面板左下角一个白块）。
   复现率 1/1。这枚按钮恰好是"我不想现在用 AI"的退出口，是赶时间用户第一个要找的。
2. **向导副标题：3.94:1（需 4.5）**。"三步完成。选择目的地、告诉我们怎么玩，剩下的交给 CityNexus。"
   字 `rgb(95,108,128)` 于纯黑，**13 px** 小字号 ⇒ 走 4.5 档。第 1 步与第 2 步都在（同一个常驻页头），复现率 2/2 屏。
   证据 `23_dark_wizard_subhead_contrast.png`。
3. **对照组（重要）**：hub 与 Today 全量文字扫描 **0 例不达标**。所以这不是"深色整体没做"，
   是 `.v8-outline-button` 这类**组件级漏网** + 一处 13 px 次要文案。
   ⇒ 建议直接进 `e345b9d6` 的三道深色门槛，而不是另开一单。
最小回归点：把上面两个节点纳入"可见文字对比度 ≥4.5"的门，断言读计算样式而不是 `data-*`（我这次就是读 `getComputedStyle`，
并且**没有**用 `data-contrast-role` 当依据——那三个节点该属性都是 `none`）。

##### T-3 `TRUTH_DEFECT`：不足一天的行程被显示成"2 天"，而且这个数还会去除预算

**我在别人车道的新加坡行程上读到屏幕原文**：`新加坡之旅 / 2 天 · 1 人 · 每人每天约 ¥200`，
而同一屏的时间范围是 `9月26日 08:00 — 9月26日 20:00 · 1 位旅行者 · 2 天` ⇒ **同一天 12 小时，写着 2 天**。
**公式（只读代码）**：`frontend/src/app/V8Experience.tsx:1492-1495`
`tripDayCount = max(1, round((end-start)/86_400_000) + 1)`。
**我用两个独立观测反推验证了它**：
- 新加坡 12 h → `round(0.5)=1` → `+1` = **2** ✓ 与屏幕一致
- 我自己那趟天津 09-21 10:00 → 09-23 20:00 = 58 h → `round(2.417)=2` → `+1` = **3** ✓ 与 hub 显示的"3 天"一致
⇒ 对跨天行程这个"含首尾"的惯例是合理的；**出问题的是同日/<24 h 那一档**：任何 ≥12 小时的当天行程都会报成 2 天。
**连带后果**（这才是我觉得值钱的点）：同一个 `safeDays` 被拿去算钱——
`V8Experience.tsx:1424` `perDay = budget / safeDays`、`:1433` 渲染"每人每天约 ¥X"。
⇒ 当天往返的用户看到的"每天可用额度"**被砍成实际的一半**。
**复现率**：用户可见侧 **1/1**（别人的行程，**不是我输入的**）；公式侧 2/2 观测吻合。
**我没有自己建一趟同日行程去验证**——那会再翻一次全局 ACTIVE 并触发 `stay-options/generate`，
按 §7 现在不该加这种负载。所以这条请归属车道用 fixture 钉死。
分类 `TRUTH_DEFECT`。疑归：`V8Experience.tsx:1492-1495`（显示）与 `:1424`（算术）。
最小回归点：`start=end 同一天` 的 fixture 断言屏幕写"1 天"，且"每人每天"金额等于总额÷人数。

##### T-4 `HUMAN_STATE_LOSS`：AI 需求里打的字一刷新就没了，应用没有草稿

我在 AI 面板输入 39 个汉字（"我希望第三天上午去古文化街，中午吃簋街小馆，下午不要太累，晚上在海河边坐一坐。"），
`textarea.value.length` 实测 **39**，然后整页刷新：面板不再打开、文本框为空、
`localStorage` 里**没有任何**匹配 `draft|intent|plan-ai` 的键。
⇒ 不是"我没存进去"，是**根本没有这个键**。
对照：同一个应用**是会**用 localStorage 的（`citynexus.v8.journey_id` 与 8 条 `copilot.history.*` 都在），
所以"这条路径没接草稿"是缺口而不是设计取向。
复现率 1/1。分类 `HUMAN_STATE_LOSS`。
最小回归点：输入→刷新→重开面板，断言 `textarea.value` 仍是那 39 个字。

##### H-6 第三次复现，且是第三座城市

新加坡行程的 AI 面板里，placeholder 与两枚快捷建议**仍然是厦门**（`我和朋友两个人去厦门…` / `带爸妈去厦门三天…`），
见 `24_dark_ai_sheet_later_button.png`。⇒ 天津、厦门、新加坡 **3/3**，建议内容与当前行程城市完全无关。

##### 我这轮主动放弃的两个动作（不是遗漏，是遵守 §7 / 避免损坏他人读数）

1. **没有打开 `/v8/stay`（住宿页）**。当前 ACTIVE 是**新加坡**这趟冷城市，而住宿页是 ORD-0065 点名的
   `stay-options/generate` 三个调用点之一（`V8Experience.tsx:525`、`:572`、`HotelsPanel.tsx:64`）——
   一打开就会打一条 ~115 秒的冷 provider 路径，正是 Amendment J §7 现在禁止的。
   ⇒ ORD-0065 要的"四种 `outcome` 终态文案可区分"这条**我没有读数**，等 §8 重建 + 套件跑完再补。
2. **没有清 `localStorage`**。共享 profile 下那枚 `citynexus.v8.journey_id` 是**所有车道共用**的，
   清掉等于把别的车道踢回向导。⇒ 我全程只读它、不写不删。

##### 收尾

- 证据累计 **24 张**在 `D:\moodle\HJ-P3_evidence\`（`23_`/`24_` 是本轮深色对比度的直接截图）。
- 全程只读：未改产品文件、未建分支、未推送、未新建隧道、未绕过 UI 调 API、未清共享状态；账本内无凭据。
- **请 §8 重建预览后 ping 我**，我要重跑的是：T-1/T-2（若 topbar 或组件样式被改）、T-3（同日行程）、
  以及本轮欠着的 ORD-0065 住宿四终态。

### commander 亲测 @2026-09-21 01:4x —— 预览已重建到检查点 `1e942d2`；向导修复我读屏复验通过，**并抓到一处新缺口**

**先记运维动作（Amendment J §8：检查点后必须重建预览，并记 `preview HEAD == checkpoint HEAD`）**
```
源：HEAD 1e942d2b77e96deb462682aca606e5ed509413e4 的 frontend/src
    拷贝保真核验：frontend/src **62 个文件逐字节相同 / 0 不同 / 0 缺失**
构建：包外副本 vite build **exit 0**（precache 9 entries / 2327.13 KiB）
部署：就地覆盖 _qoder_preview_20260920/dist（不停进程、不开第二条隧道）
入口：/v8/live 200 且已引用新 bundle **assets/index-vu8FxqTN.js**；/api/v1/health 200
⇒ **preview HEAD == checkpoint HEAD（1e942d2）成立**
```
⚠ 注意：这只覆盖 **frontend**。`8c66aa92` 手上 ORD-0063/0064 的后端改动**仍在工作树未提交**
（`temporal.py` +132 / `stay_mobility.py` +63 / 新测试文件），所以**后端不是这个检查点的一部分**。

**向导修复读屏复验（脚本 `raw/verify_1e942d2.cjs`，读数 `raw/verify_1e942d2b.json`，390×844 触摸上下文）**
```
留空抵达/离开： next.disabled = **true**            ← 合并前是"可点且零反馈"
               屏幕可见原因 = 「**还需要填写：抵达地点、离开地点**」   ← 指名到字段，是中文人话
填齐后：        next.disabled = **false**（按钮恢复）
超 7 天：       审核页显示真实地点「Tianjin West Station · 2026-10-09 18:00」
               （合并前是裸「— · 2026-10-09 18:00」）
               提交后屏幕 = 「这一步没有成功，行程还没有创建。 The trip is longer than the supported
               journey window of 7 days. Shorten the dates and try again.」；后端 422 码正确
```
⇒ 车道 ORD-0056 声称的三症状，**我在权威生产构建上逐条复现为已修**，`verdict: ACCEPTED`。

**但我抓到一处它没提的新缺口（这条是它自己注释里承诺过的东西）**：
- `next.disabled=true` 时，`aria-describedby = **null**`，`[role="alert"]/[aria-live]` 命中 **0 个**。
  ⇒ 那句「还需要填写：抵达地点、离开地点」**只对眼睛可见，对读屏软件不可达**。
  而它自己在 `JourneyTrialSetup.tsx` 里承诺过"带 ARIA wiring"（我 17:3x 给它的要求 (a) 里也写了
  "渲染一行可读提示 + `aria-describedby`"）。⇒ **一半做到了，可访问性那一半没做**。
  这不是我苛求：本项目的无障碍门（<44px 那条）就是同一个方向，且 Mission 003 的 M3-C 契约要求
  "可读"——对使用读屏的用户，这条提示等于不存在。
- 顺带一条正面结论：`relaxed` 这类内部枚举我这次没在向导首屏看到（HJ-P3 报过），
  但它报的是另一处表面，**不作为本次结论**。

⇒ 新开 **ORD-0066**（把这条提示接进 `aria-describedby` + 让它被读屏播报），归 `e345b9d6`。



## ORDERS（收件箱：worker 每完成一个动作、每开始下一个动作之前先读这里）
认领规则：只认领 `to` 等于自己会话 id 前缀的 OPEN 条目；认领时立刻改成 `CLAIMED@时间戳`；
先把手上这一步收尾到自洽状态（不留半改文件、不留脏树）再接新单；做完改 `DONE@时间戳` 并在
`evidence` 写清 collected/deselected 条数与关键断言；不认领别人的单、不改别人的文件；
不为了接单去 rebase/reset/clean。若你已在比 `if_head` 更新的 HEAD 上，先复核订单是否还成立，
不成立就地标 `SUPERSEDED`，不要按过期指令改代码。
**记账格式（07:16 新立，起因是实测多条订单出现两个 `status:`）**：每条只允许**一个** `status:`
与**一个** `evidence:`。交付时**改写那一行**（CLAIMED→DONE@时间），把新证据**追加进同一个
`evidence` 块**；不要新增第二个 `status:`/`evidence:` 键——那样榜单会先读到 CLAIMED 而把你
已完成的活计成未做（今晚 ORD-0015/0022/0030/0031 都踩到了），也让后来的人在歧义里猜进度。

```
- id: ORD-0060
  to: e345b9d6
  priority: high
  if_head: 576fbf6
  order: |
    **向导文案与未识别城市的可见反馈（HJ-P1 实测 + 我源码证实）。** 三件事都在
    `frontend/src/features/setup/JourneyTrialSetup.tsx`：
    1. `:296` / `:305` 的中文标签把城市名**硬编码成"厦门"**（`抵达厦门` / `离开厦门`），
       而英文分支 `Arrive at` / `Depart from` 不带城市 ⇒ **只有中文界面在骗人**。
       一个要去东京的人在填"抵达厦门"。改成跟随**当前已识别目的地**；
       占位符 `:281` / `:301` / `:310` 同理，不得复用上一次识别结果的残留示例。
    2. `:220` `step1Ready = draft.cityName.trim().length > 0` —— 只看非空、不看是否被识别，
       所以 `拉萨` / `西安` / 乱码都能"下一步"，而 `:209/:219` 的隐藏字段仍保留**上一个城市**的
       `country=CN / currency=CNY / timezone=Asia/Shanghai` ⇒ 静默沿用错误口径继续往下走。
       要么屏幕上明说"没认出这个城市，将按 CN/CNY/上海时间规划，或换个写法"，要么禁用创建并说明原因。
       **注意**：只把按钮 disable 不算修完（仲裁原话：disabled button without an inline explanation
       is still a silent blocker）。
    3. 城市清单不可见（5/5 屏都没有"目前支持 N 个城市"的入口）。给一条**可见入口或一句说明**；
       权威城市数由我在交接文档里钉死，**不得**前端自己另算一套。
    **边界**：`inferCityFacts` 是本地表（`:25` 那种硬编码字典）——**不要**为了这条去调后端做识别校验
    （那是另一件事，需要契约）；不得削弱冻结清单；断言一律读 `innerText` 渲染文字，不读 data 属性。
    **验收**：中文界面下输入东京时屏幕必须出现"抵达东京"（且不再出现"抵达厦门"）；
    输入未识别城市时屏幕必须有一句可读提示；两条都给杀得掉的证据（点名节点 id）。
  status: DISPATCHED@2026-09-20 22:2x

- id: ORD-0062
  to: 8c66aa92（后端归因）+ e345b9d6（前端说实话）
  priority: urgent
  if_head: 576fbf6
  order: |
    **AI「帮我规划」返回 HTTP 200 却说"没有生成可行方案"，用户无法区分三种完全不同的原因。**
    HJ-P3 实测 4/4 失败（天津热城市、同一句重试、厦门、**以及一句无约束"随便安排一下就行"** 都失败）；
    我在预览后端日志核到 `POST /api/v1/journeys/{id}/agent/commands` **11 次全部 200 OK**。
    ⇒ 形状与已结案的 `stay-options top_k=[] + 200` 同一类：**状态码说成功，界面说没结果，中间没有原因**。
    要求（照 ORD-0049 已被接受的做法做，先测量再改）：
    1. 给 agent 规划路径加**分段计时与阶段结果**（是否真的调用了外部 AI、输入是什么约束、
       候选从哪来、可行性判定在哪一步把它判死、有没有被 `HARD_FEASIBLE_QUALITIES` 挡掉）；
       **不要**先猜是 AI 的问题——日志级别不记 provider 流量，我没法从外部证明它被调用过。
    2. 响应体必须带**机器可读的 no-plan 原因码**（区分：约束互相矛盾 / 数据不足以判定 / provider 降级 /
       外部 AI 未启用或失败 / 超时），前端据此说一句人话；
    3. **无约束请求也失败**这一点单独查：一句"随便安排一下"若也拿不到方案，说明不是用户约束过严，
       而是链路某处恒拒。这条优先。
    4. 验收：一条门断言"no-plan 响应必须带原因码，且屏幕上渲染的是该原因的人话"，
       断言读 `innerText`；再给一条杀得掉的证据（去掉原因码即红，点名节点 id）。
    边界：**不得**为了让 AI 面板"看起来成功"而生成无依据内容（provenance / `fact_quality` 冻结）；
    **不得**把未知当已知；不得关掉真实调用来自证；外部 AI 失败必须如实显示为失败。
    回报：先给时序与阶段证据，再给结论。
  status: DISPATCHED@2026-09-20 22:4x


### commander 独立复核 @2026-09-20 23:0x —— ORD-0032 三数复算完毕 → `DONE`

我用 `raw/check_stage_vs_head.py`（逐文件 `git ls-tree` + `sha1("blob %d\0"+bytes)` 与 HEAD 比字节）
在 HEAD `576fbf6` 上重跑，**与 `6af4cf53` 自述逐字相同**：

```
HEAD tracked blobs = 6704   |   包 = 714 文件
byte-identical to HEAD : 710      ← 车道报 710 ✓
DIFFERS from HEAD      : 2        ← 车道报 2 ✓
IN STAGE, NOT IN HEAD  : 2        ← 车道报 2 ✓（两份交接文档）
hygiene: forbidden-path hits = 0  |  real-key hits in stage = 0
```

**两个"有意不同"我查到了具体身份，都成立且都该不同**：
1. `qoder-handoff/qoder_xiaomi_truth_hardening_v6.patch` — `head=03b0ff82c` vs `stage=6e9e090ab`。
   `6e9e090ab` **正是我 21:0x 从 GitHub 那条 v6 分支取回比对过的同一个 blob** ⇒ 包里带的是
   **已 sanitize 的那一份**，与"包内真实 key 命中 = 0"互相印证；而 HEAD 那份仍带 key（`HUMAN_ATTENTION_REQUIRED` 第 1 条）。
   ⇒ **这条不是巧合能凑出来的，是同一 blob sha 对上同一结论。**
2. `tools/verification/mutation_campaign.py` — `head=f4ff78da9` vs `stage=6d36a2297`。
   `6d36a2297` 是**我自己那把未提交的硬化版量具**（账本记的 HEAD/工作树两值之一）⇒ 包里带的是量具最新版，
   归属正确（这文件 2026-09-20 起归 Commander）。

**"仅包内 2"也核了**：`convergence_summary.md` 1,765 B、`handover_authoritative.md` 3,708 B，都是交接件，不是代码。

`verdict: DONE`（包内容对齐与卫生两项达成）。**两条仍然欠的，不算被这单吸收**：
① verifier 三条红照旧（`playwright.sw.config.ts` / `qoder-sw-lifecycle.spec.ts` 等 ORD-0043；
   `qoder-user-critical-path.spec.ts` 等 ORD-0039，**故意保持红**）；
② 仲裁 `5749459724` §4 明令 **"必须对 exact packaged candidate 跑 runtime gates，
   不能拿相邻工作树的绿色给包签字"** ⇒ 这一条我记成 ORD-0032 的**后续门**，
   等 ORD-0043/0039 落地后对包内副本重跑一次全量，再出 `@HEAD + 两次连跑` 读数。


- id: ORD-0063
  to: 8c66aa92
  priority: urgent
  if_head: 576fbf6
  order: |
    **TRUTH_DEFECT：当天往返 12 小时被判成"2 天"，参考值因此算错。**
    定位（我在 `576fbf6` 上按字符串核过，不是照抄车道路线）：
    `frontend/src/app/V8Experience.tsx:1469`
    `Math.max(1, Math.round((endMs - startMs) / 86_400_000) + 1)` ⇒ 08:00→20:00 得 **2**；
    `:1397 safeDays = Math.max(1, days)` 只是兜底，**没有纠正这个口径**。
    实测屏幕原文：「新加坡之旅 **2 天** · 1 人 · 每人每天约 ¥200」，
    而同一屏下一行又写「9月26日 08:00 — 9月26日 20:00 · 1 位旅行者 · **2 天**」⇒ 自相矛盾。
    要求：
    1. 先查清产品对"天"的权威口径到底是**日历天（含首尾）**还是**24 小时窗口**——
       `backend/app/core/temporal.py` 那套 `derive_journey_temporal_shape`（账本记的是
       "Oct 1 -> Oct 4 是 4 天 / 3 夜"）应当是**唯一真值来源**，前端不得自己再算一遍；
    2. 前端改成消费后端给的天数，**删掉本地那套 `Math.round(...)+1`**；
    3. 如果后端本身对"同日往返"也给 2，那是后端缺陷，一并修，并给跨午夜与同日两种用例；
    4. 验收：同日 08:00–20:00 断言 `天数 == 1` 且 `每人每天 == 总预算 ÷ 人数`；
       跨午夜与多日各一条；断言读 `innerText`；给杀得掉的证据（点名节点 id）。
    边界：不得改动 `MIN_JOURNEY_DAYS` / `MAX_JOURNEY_DAYS` 的 7 日窗口语义（ORD-0033 已验收）；
    不得为了凑数把"夜"和"天"混用；冻结清单一律不动。
  status: PARTIAL@2026-09-20T22:2x+08 by 8c66aa92（后端半 DONE：提交 `3f1b44c`，temporal_shape/budget_reference + 13 门 + 7/7 变异；第 2 条与屏幕验收要写 e345b9d6 的 V8Experience.tsx ⇒ 补丁已交 review/ORD-0063-0064a-frontend.diff，等 (α)/(β) 裁决，见 DELIVERIES 同名块）

- id: ORD-0064
  to: 8c66aa92（符号与算术）+ e345b9d6（住宿页承诺与失败文案）
  priority: urgent
  if_head: 576fbf6
  order: |
    **TRUTH_DEFECT / HUMAN_MISLEADING 三件，同一个用户可见后果：屏幕上的钱数不可信。**
    (a) **币种符号硬编码**：`V8Experience.tsx:1408` 的模板把 `¥` 写死，
        所以新加坡行程显示「每人每天约 **¥200**」而「我的」页同一分钟显示「**SGD 400.00**」；
        东京行程显示「每人每天约 **¥5**」而向导写「JPY 1500」。
        ⇒ 符号必须取自该行程的币种；`:1397` 附近若还固定 `toLocaleString("zh-CN")` 也一并跟随 locale。
        验收：非 CNY 行程的标题行**不得出现 `¥`**（复现率 2/2：东京、新加坡）。
    (b) **页头承诺与同屏自相矛盾**：`src/i18n/LocaleContext.tsx:1212`
        「每个费率都明确标注币种、房型、入住人数、退改政策、新鲜度…」，
        而 `StayExplorer.tsx:124-133` 在 8/8 个候选上都只能显示「价格未知（供应商未提供房价）」。
        ⇒ **不要**为了兑现承诺去编价格（OSM 本来就没有房价，这个取舍我认，卡片写"价格未知"是对的）；
        要改的是**那句承诺**：价格不可得时不得宣称"每个费率都明确标注币种"。
        验收：当全部候选 `price_minor <= 0` 时，屏幕上不得出现"明确标注币种"这句。
    (c) **失败文案把成因指向用户无法验证的量**：AI 规划失败说「可以调整预算或换个说法再试」，
        而同一条行程的住宿页刚说没有房价 ⇒ 用户不可能知道该调到多少。
        ⇒ 失败文案必须把"本次没有可用价格数据"这一成因写进同一句（或与 ORD-0062 的原因码联动）。
        这条与 ORD-0062 成对：**先有原因码，文案才谈得上说实话**。
    边界：**不得**为了让符号好看而伪造汇率换算；**不得**把未知价格印成 0 或"免费"；
    不得削弱 provenance / `fact_quality`。断言一律读 `innerText`。
  status: PARTIAL@2026-09-20T22:2x+08 by 8c66aa92（(a) 后端半 DONE@`3f1b44c`：币种随行程 + CNY 地板不可比标记，13 门里含 JPY/无预算两例，7/7 变异；(a) 显示层与 (b)(c) 归 e345b9d6，前端补丁同上）


- id: ORD-0065
  to: e345b9d6
  priority: high
  if_head: 576fbf6
  order: |
    **区分"行程已创建"与"方案没出来"这两件事。** 我在源码里看到
    `V8Experience.tsx:584-585` 的提示是「行程已创建。告诉 AI 你想怎么玩，它会生成可选方案。」/
    "Trip created. Tell the AI how you like to travel…"，它只反映**行程行存在**，
    不反映后续 `stay-options/generate` 或 AI 规划是否成功。
    已知实测事实（不必重测，直接用）：
    - 冷城市首次 `stay-options/generate` 可耗时 ~115 秒并返回空（`e981b46` 后带 `outcome` 四类码）；
    - AI 规划在预览上 **11 次调用全部 HTTP 200，屏幕说"没有生成可行方案"**（ORD-0062 在查成因）；
    - 前端三个 `stay-options/generate` 调用点（`V8Experience.tsx:525`、`:572`、`HotelsPanel.tsx:64`）
      **全部丢弃返回值**，后端新加的 `outcome` 等字段前端零消费（红队实测）。
    要求：
    1. 行程创建成功但方案/住宿生成失败或为空时，屏幕上必须**同时**说清两件事：
       行程已经在（可继续），以及这次没出方案**以及为什么**（用后端 `outcome` 码，别自己猜）；
    2. 不得用一句"行程已创建"覆盖后续失败，也不得把空结果画成"正在加载"；
    3. 消费后端 `outcome`：`OPTIONS_FOUND` / `NOT_APPLICABLE_ZERO_NIGHTS` /
       `NO_OFFERS_FROM_PROVIDER` / `ALL_CANDIDATES_REJECTED` 四种终态**文案必须可区分**；
    4. 验收：断言读 `innerText`；给"后端返回 `NO_OFFERS_FROM_PROVIDER` 时屏幕不得出现
       '正在为你寻找住宿'或空白"这类可杀死的门（点名节点 id）。
    边界：不得伪造方案或把未知写成已知（provenance / `fact_quality` 冻结）；
    不得为了让界面好看而隐藏失败；后端契约不动。
  status: DISPATCHED@2026-09-21 00:2x


- id: ORD-0066
  to: e345b9d6
  priority: high
  if_head: 1e942d2
  order: |
    **向导的"还需要填写"提示对读屏软件不可达（我在重建后的生产构建上实测）。**
    读数（`raw/verify_1e942d2b.json`，390×844 触摸上下文，只读渲染/属性）：
    ```
    留空抵达/离开 → next.disabled = true          ✓ 修好了
                    屏幕可见原因 = 「还需要填写：抵达地点、离开地点」  ✓ 人话、指名到字段
                    但 aria-describedby = **null**、[role="alert"]/[aria-live] 命中 **0**
    ```
    ⇒ 这句话**只对眼睛可见**。你在 `JourneyTrialSetup.tsx` 的注释里承诺过 ARIA wiring，
    我 17:3x 的要求 (a) 里也写了"渲染一行可读提示 + `aria-describedby`"——**只做到了一半**。
    要求：
    1. 那条提示容器挂 `role="alert"`（或 `aria-live="polite"`），并在出现/变化时被播报；
    2. 把它接到被禁用的主按钮上：`aria-describedby` 指向该提示的 id（缺项变化时 id 稳定）；
    3. 字段级错误同样要可被读屏定位（`aria-invalid` + 指向该字段的 `aria-describedby`）；
    4. 验收：断言读 **ARIA 属性与可访问性树**（不是 `innerText`）：留空时
       `next[aria-describedby]` 非空且指向的元素文本包含"还需要填写"；给一条杀得掉的证据
       （摘掉 `aria-describedby` 即红，点名节点 id）。
    边界：不改判定语义（该禁还是禁）、不改文案（已经很好了）、不削弱冻结清单；
    `V8Experience.tsx` 已按 Amendment J §2 归你，可一并改。
  status: DISPATCHED@2026-09-21 01:4x


- id: ORD-0001
  to: 8c66aa92
  priority: urgent
  if_head: 4d2f0c8
  order: 修 backend/app/operations/v9.py::_execution_truth —— 游标 STALE 时仍投影 next_leg_id/next_mode/next_eta_min。
         把腿的绑定条件从索引改成"存在可信 Now"：next_leg = legs[current_index] if now_item is not None and 0 <= current_index < len(legs) else None
         并补两条回归：(a) legs 多于 activities 且游标 STALE → next_leg_id/next_mode/next_eta_min 全空；
         (b) cursor_status=VALID 且 next_activity_id 非空 → next_state 不得为空（v9 与 Edge/v10 一致）。
  status: DONE@20260920-034901
  evidence: Commander 沙箱独立重现（HEAD 4d2f0c8 + 未提交文件，指纹稳定）：
            {"cursor_status":"STALE","now":null,"next":null,"next_leg_id":"80e9018e…","next_mode":"AUTO","next_eta_min":29}
            违反 Mission 002 A 节 stale 投影要求（Now/Next/NextLeg 必须全空）。
            [8c66aa92 DONE@20260920-034901] HEAD 00dfd62；修法照你给的语义：next_leg 只在 now_item is not None 时在界内取。新增 tests/test_qoder_next_leg_binding.py 4 collected / 4 passed（parametrized 两个 id：[act-from-superseded-plan-STALE]、[None-ABSENT_FALLBACK]，第二条腿泄漏是你没点名的 ABSENT_FALLBACK 完成态）。突变验证（唯一 anchor+compile+字节还原 sha256 校验）：把守卫退回索引式 -> 4 failed / 12 passed，killer 含本文件 2 条与权威层 2 条。全量 899 passed / 15 skipped / 0 failed（895+4）。
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
  status: DONE@20260920-032x by commander（仲裁 Amendment B 授权修 QA harness；8c66aa92 曾于 03:15:44 CLAIMED，已通知停手以免双写覆盖）
  evidence: 我沙箱实测 `--only RX1 RX2`：baseline 102 passed；RX1 anchor missing(skip)；RX2 KILLED(1 failed/101 passed)。
            另 11 个 anchor 的对应关系：多行→字节精确 False/LF 归一 True；单行→两者 True。
            已落地改动（`tools/verification/mutation_campaign.py`，py_compile exit 0，diff 148/30）：
            LF 归一匹配 + 按原行尾写回；四类判定 KILLED / SURVIVED / HARNESS_INVALID / EQUIVALENT_OR_NON_ACTIONABLE；
            preflight 在 anchor 缺失时 return 2 并打印 PREFLIGHT FAILED（不再静默 skip）；
            逐突变输出 ran/passed/failed/skipped/error 与杀它的测试名；新增 3 个可执行突变
            C4G(`app/services.py`)、C4A(`app/planning/anchor_schedule.py`)、RX3NEXT(`operations/v9.py` 陈旧游标回退首活动)。
            我自己引入并被自己抓到的两个 bug（记录以免有人重走）：
            ① 用 `Path.write_text` 写回把 LF 文件翻成 CRLF，diff 一度变成 398/315 全文件抖动 —— 已归一回 LF；
            ② `pytest -q --no-header` 根本不打印 "N collected" 行，导致我的 collected 解析恒为 0 而拒绝跑突变
            —— 改为从 summary 解析 passed/failed/skipped/error 并以此判定"是否真的执行过"。


- id: ORD-0004
  to: dc19d662
  priority: normal
  if_head: 4d2f0c8
  order: 在你自己的原始目录（不要复制到其他路径）把 test_v3_concurrency.py 连跑 5 次，逐次报每条用例的 PASS/FAIL；
         特别是 test_three_way_race_one_winner_and_the_canonical_state 在你改写断言后是否仍会偶发失败。
         若仍偶发，给出最小调度重现与它违反哪条不变式；若 5/5 全过，就把它标为已闭合并说明原因。
  status: DONE@2026-09-20T03:22+08:00
  evidence: 原地连跑（未复制）。collected 恒为 4、deselected 恒为 0（`--collect-only` 头行：
            "4 tests collected in 1.09s"）。共 10 轮全绿：03:20:19–03:20:54 五轮 + 03:21:16–03:21:43 五轮
            （第二轮起改用 `-rA` 取逐用例清单，故跑了 5+5）。每轮 4 passed / 0 failed，
            四条用例名逐轮均 PASSED：test_restart_then_retry_of_the_same_key_never_transitions_twice、
            test_one_key_spent_on_two_different_proposals_is_not_a_silent_replay、
            test_three_way_race_one_winner_and_the_canonical_state、
            test_capture_after_accept_then_a_second_accept_attempt。
            ⇒ three_way_race 已闭合并说明原因：旧断言写死 `statuses.count(200)==2`，即假定"a 提案赢"；
            竞态胜者本就是非确定的，实测出现 [409,200,409]（b 赢 + a 的重放正确地不被伪装成成功）。
            改为调度无关判据后：两个不同 proposal 恰好一个 200、第三方重放当且仅当重放胜者时才 200、
            且 DB 真值必须 1 ACTIVE plan / 1 ACCEPTED / 指针一致 / 0 悬挂 ACTIVE C4。
            该用例在 HEAD 4b1e829 的并发负载下（同期另一进程正在跑全仓 904 条突变套件）也 5/5 通过，
            负载下通过比安静态更强。日志 raw/ord0004_five_runs.txt。
            注：test_restart_then_retry… 依赖原地相对路径（WinError 267 只在被复制后出现），复现须原地。
            本会话另按 ORD-0004 之外自测得：HEAD 上 6 突变仅 M3 存活（904 collected/0 deselected）、
            main.py 四处 C4 谓词单点降级在 9759633 与 4b1e829 上均为 2/4 KILLED（883 与 904 collected，
            deselected 恒 0），存活的是 _trip_studio_authoritative_gate 与 _revalidate_locked_commitments。

- id: ORD-0005
  to: 6af4cf53
  priority: normal
  if_head: n/a
  order: 今夜只准备不推送。产出排除清单 + 完整文件清单 + 密钥扫描结果到 D:\moodle\_qoder_publish_manifest_20260920\，
         排除至少含 _qoder_recovery_20260919 / _qoder_rx4_20260920 / _qoder_verifier_20260920 / _codex_sol_* / _astra_* /
         各类一次性克隆与 *.db / .venv / node_modules / __pycache__ / test-results / playwright-report。
         不得访问 github.com 的 git 协议（会弹登录框）。
  status: DONE@20260920-042000
  evidence: 交付 D:\moodle\_qoder_publish_manifest_20260920\ 四件套：
            - summary.md（结论摘要 + 排除清单 + 扫描判定）
            - exclusions.json（排除目录 4630 条 + 按规则文件统计）
            - filelist.tsv（候选完整清单 383175 行）
            - secretscan.json（55 条命中明细含判定）
            collected = 383,175 files / 3,659.5 MB；
            deselected = 4,630 dirs + 38,794 files；
            密钥扇 55 命中 = LIVE-EXCLUDE 0 / ALREADY-LEAKED 0 / REVIEW 51（全误报）/ PLACEHOLDER 4。
            关键断言：
            (1) 候选集内活跃密钥命中 = 0（首轮 4 处 node-compile-cache 私钥已由目录规则挡掉）；
            (2) 已泄漏 key sk-5343f86b… 在候选集内已就地替换，复扫归零；
            (3) 51 条 REVIEW 全部为 DEEPSEEK_API_KEY= 空值跨行误匹配，模板文件中真实值匹配数 = 0；
            (4) .api_tok_20260920 随 _qoder_recovery_20260919 整体排除，未进入候选集。
            未完成/待复核：CityNexus-History 分批推送在第 6 批前被停机，远端是否已收到前几批
            无法确认（按指令未再访问 github.com）；本地 commit 保留未推。
            本会话未执行 git push / git fetch / git credential fill 访问 github.com。

- id: ORD-0006
  to: 8c66aa92
  priority: urgent
  if_head: 4b1e829
  order: 按仲裁 Mission 002 Amendment B 落地 STALE 投影硬门。cursor_status == "STALE" 时权威投影必须
         now / now_activity_id / next / next_activity_id / next_leg_id / next_mode / next_eta_min 全为 null，
         now_state == "STALE_CURSOR"（即 ORD-0001 的修法：NextLeg 只在存在可信 Now 时才投影）。
         新增权威回归：ACTIVE 计划 + 存在但不可解析的 current_activity_id + len(legs) > len(activities)
         （腿端点可空，属合法持久态），断言整个元组；该回归必须在"移除 trustworthy-Now 守卫"的一次性突变下失败。
         此门独立于 16 突变分母，不得塞进分母凑数。
  status: DONE@20260920-034901
  evidence: Commander 沙箱重现（HEAD 4d2f0c8 + 未提交文件，指纹稳定）：
            {"cursor_status":"STALE","now":null,"next":null,"next_leg_id":"80e9018e…","next_mode":"AUTO","next_eta_min":29}
            [8c66aa92 DONE@20260920-034901] 同一提交 00dfd62。权威回归落在 tests/test_sol_execution_cursor.py：test_a_stale_cursor_with_more_legs_than_activities_nulls_the_whole_tuple + test_a_finished_journey_with_extra_legs_projects_no_departure_step，各 1 collected；断言整元组 now/now_activity_id/now_state/next/next_activity_id/next_state/next_leg_id/next_mode/next_eta_min 加 cursor_status，并同时核对持久快照、/offline-snapshot 与 Edge 设备视图。该门未进 16 分母。诚实边界：本树无任何出厂路径产出 len(legs)>len(activities)（demo 计划 0 条腿；三处写入者 v9.py:668 / main.py:4628 / authoritative_v12.py:1383 都按相邻活动成对写，恒为 activities-1），所以这是契约加固而非复现；你的 AUTO/29 指纹若来自真实计划，那条多写腿的路径是另一个缺陷，我没有顺手吸收。突变：移除守卫 -> 4 failed / 12 passed（killer 见 evidence 上一条），字节还原校验 True。
- id: ORD-0007
  to: 8c66aa92
  priority: urgent
  if_head: 4b1e829
  order: 新增跨消费者差分不变式：v9 暴露非空 next_activity_id 时 Edge/V10 必须对同一活动给出非空 next state；
         若语义上确实没有下一步，则 v9 也必须给 next_activity_id = null。不允许两个消费者对"是否存在 Next"意见不一致。
  status: DONE@20260920-034901
  evidence: 重现用例 test_v1_cursor.py::test_terminal_cursor_with_pending_steps_keeps_next_consistent_across_consumers
            （cursor_status=VALID、next_activity_id 非空、Edge next_state=None）。
            三向竞态按仲裁指示保持 UNCONFIRMED，不计入产品缺陷与账面。
            [8c66aa92 DONE@20260920-034901] 00dfd62。edge_snapshot 之前用 legs=[] 调共享投影、再自己按 now_activity_id 反推 index（推不出就落 len(activities)），于是同一份响应里 execution 与设备字段对“有没有 Next”各执一词；你复现的形状正是 cursor 落在已完成活动、后面还有 PENDING。现在 Edge 取同一份腿列表、只问一次 _execution_truth，now/next/mode/eta 全部取自该答案，并新增顶层 next_leg_id 供设备直接引用。新增两向差分门各 1 collected：test_edge_and_v9_agree_on_whether_a_next_step_exists（有 Next 必须两边都给状态）、test_edge_and_v9_agree_when_there_really_is_no_next_step（没有 Next 两边都给 null）。突变验证：让 Edge 再自己反推 -> 1 failed / 15 passed，killer 是前者；后者在反推下仍通过，所以两个方向都留了独立节点。三向竞态按你的指示未动、未计入账面。
- id: ORD-0009
  to: e345b9d6
  priority: normal
  if_head: 00dfd62
  order: UI 车道设单已复核 —— **APPROVED（带四条限制）**。
         批准 write-set：frontend/src/design-tokens.css、styles.css、v10.css、
         features/setup/JourneyTrialSetup.tsx、features/inbox/JourneyInboxWorkbench.tsx、
         新建 components/v8/StateBlocks.tsx；证据与截图一律落 _qoder_ui_overnight_20260920\review\。
         四条限制：
         (1) 把 --v8-* 从 .v8-product-shell 上提到 :root 属于全局重皮，必须先拍 before、改完立刻跑
             现有 qoder-contrast-audit 与 qoder-mobile-overflow 两道门，任何一条变红就回退该步；
         (2) index.html 加 viewport-fit=cover 必须与真实 padding 同批落地，不许只加 meta（那样内容会钻到 home 指示条下）；
         (3) 先做零生产写入的那件：把移动门禁口径扩到 360/390/412/915 并纳入 Journey 创建与 Wallet，
             它是后面所有改动的回归网；
         (4) V8Experience.tsx 仍归 8c66aa92：只读。确实需要锚点时交"只加类名/data 属性、零逻辑"的补丁给我转交。
  status: APPROVED@20260920-040x by commander（我逐条独立复核过它的证据）
  evidence: Commander 复核（HEAD 00dfd62，frontend/）：
            `grep -rn -- "--v8-surface:" src/` = 0 命中、`--v8-accent:` = 0 命中；引用分别 3 与 15 处 → 静默走 fallback 成立。
            `--v8-*` 定义确在 design-tokens.css 的 `.v8-product-shell` 选择器下；V8Experience.tsx:819 起 `if (setupOpen) return <JourneyTrialSetup .../>` 在 shell 之外 → 首次进入拿不到自身 token 成立。
            index.html 的 viewport 无 viewport-fit=cover，而 styles.css 有 3 处 env(safe-area-inset-*) → 这 3 处算成 0，是死代码。
            styles.css 断点确为 `@media (max-width: 380px)`；e2e/qoder-mobile-overflow.spec.ts 的 WIDTHS=[360,412,430]、高度恒 844、只测 Today+Live → 390/915 与 Wallet/setup 无覆盖。
            FLASH-F3 的 BLOCKER 3 / HIGH 5 / MEDIUM 5 / LOW 4 与上述一致，其"截图未取得"已如实声明，不计作视觉验收证据。

- id: ORD-0019
  to: 1fb26149
  priority: normal
  if_head: 954edaa
  order: |
    交给你一件**只有你做过**的事：去推翻 C 节第 17 行 `F` 的等价声明。当前理由是
    "公开端点走不到该分支：丢掉已承诺活动更早就被 feasibility gate 以 `LOCKED_COMMITMENT_LOST` 拒了，
    重复它被 `ACTIVITY_OVERLAP` 拒了，所以没有合法 accept 到达这里；0/1/many 计数由
    `resolve_commitment_target()` 直接断言"。**这段话现在是被断言的，不是被测的。**
      1) 在 `D:\moodle\_qoder_rx4_20260920\` 里自己复现 F 的突变（别改权威树），确认改动位置；
      2) 穷举可达路径：承诺状态（CONFIRMED / LOCKED / 外部预订但地点不可解析）×
         提案形态（替换 / 插入 / 移动 / 同刻重叠）× accept 顺序与幂等键复用；
      3) 每条尝试给出请求体、响应码、响应错误码，以及**该分支是否真被执行到**的证据
         （用你 `RX4_GATE.md` §4.3 那套 instrumentation，别靠读代码猜）；
      4) 结论只许三种：`FALSIFIED（附最小反例）` / `NOT_REACHABLE（附穷举表）` /
         `PARTIAL（哪些没试到、为什么）`。
    若 FALSIFIED：这行从"分母之外"搬进 actionable，矩阵按 Amendment E 1b 重跑，且这是一条真缺陷；
    若 NOT_REACHABLE：`EQUIVALENT` 标签第一次拿到测量支撑。**不许**为了维持"C 节已 PASS"写第三种结论。
    边界：只读权威树；只在自己目录突变；不写生产代码；不改量具；不新建会话；不碰 GitHub；
    临时 worktree 若要用，遵守 D-7（先解链再 remove）。预算 40 分钟，到点交 PARTIAL + 已有穷举。
  status: DONE@20260920-052310 by 1fb26149（结论 PARTIAL，非 FALSIFIED 亦非 NOT_REACHABLE；穷举表见 D:\moodle\_qoder_rx4_20260920\ORD19_F_REACHABILITY.md）
  evidence: |
    为什么给你：你已有该分支的 instrumentation 与不可解析锚夹具（`RX4_GATE.md` §4.3 空转自证），
    且 ORD-0011/0013/0014/0015/0017/0018 分属其它车道，本单写域零重叠。
    你 ORD-0003 里"REQUIRED_ACTIONABLE=16 使 `--only` 子集恒为红"的顾虑我实测不成立：
    该判定写作 `if not args.only and actionable < REQUIRED_ACTIONABLE`，且 `--only F` 冒烟实打实
    打出 `CAMPAIGN PASSED`。但你建议的方向（全量前要有便宜自检）是对的，已变成硬规矩。

- id: ORD-0024
  to: 8c66aa92
  priority: normal
  if_head: a75ba7a
  order: |
    Amendment F 第 1 条落在**你的文件**里，一句话的事：
    `V8Experience.tsx` 那个让 Journey 创建落在 `.v8-product-shell` 之外的提前 return，
    仲裁裁定它是**刻意的 onboarding 行为**（首进门不要底部主导航，不为此做壳层迁移）。
    → 请在该 return 处补一段**说明它是刻意的**注释（含"pre-Journey onboarding：不给全局底部导航，
    视觉地基由 wrapper 提供"这层意思），让下一辆车道不会再把它当成漏掉的作用域 bug 去"顺手修好"。
    这是 ORD-0017 之外的第二件小事，两件都在同一个文件里，可以一批做。
    注意：UI 车道会新增 onboarding wrapper（ORD-0023），**它的注释归你、wrapper 归它**，
    别互相伸手。
  status: DONE@20260920-061937 by 8c66aa92（同一笔 `1187ce6`）；**Commander 已验**
  commander_check: |
    注释原文已读（`V8Experience.tsx` 该 return 上方 6 行）：写明"Intentional, and ruled so
    (Amendment F #1)"、没有行程就没有可导航的目标、**不要**为了文案把 return 搬进壳层、
    视觉地基归 onboarding wrapper。正是仲裁要的那种"读起来是决定而不是 bug"的注释。
    边界也守住了：只 +8/−2、只动这一个文件，没碰 UI 车道的 wrapper。
  evidence: |
    仲裁原话："document the early return as intentional: focused pre-Journey onboarding,
    no primary app navigation"（评论 5745474928 §1）。
            [8c66aa92 DONE@20260920-061937] 同一提交 1187ce6 的第二段：在 if (setupOpen) return 前加了注释，写明这是 Amendment F #1 裁定的刻意行为（pre-Journey onboarding 不给全局底部主导航、视觉地基由 onboarding wrapper 负责），并明写不要为了一块屏幕把 return 迁进 .v8-product-shell。wrapper 本体归 e345b9d6，我没有伸手；注释归我。验证：typecheck/typecheck:all/build 退出码 0；纯注释与文案，git show 1187ce6 只有这两处。
- id: ORD-0025
  to: 8c66aa92
  priority: urgent
  if_head: 9e66d1e
  order: |
    **我今晚发现的最严重的一条量具缺陷，在 e2e 这一侧，归你（`playwrightEnv.ts` / `playwright.config.ts`
    刚被我划进你的写域）。** 完整复现与逐条对照在
    `D:\moodle\_qoder_recovery_20260919\reports\E2E_REFUSE_SILENT.md`，一句话：
    **authoritative 模式的"拒绝启动"既不出声、也不非零。**

    最小复现（同一目录、同一 shell，Node v24.14.0 / Playwright 1.63.0，用 `node node_modules/@playwright/test/cli.js`
    而不是 npx）：
      A) 不加 `CITYNEXUS_E2E_AUTHORITATIVE=1` → `--list` 正常打印 4 个节点，stdout 523 B；
      B) **只加这一个变量** → stdout 0 B、stderr 0 B、**exit 0**。
    B 本该在 `requiredEnv("CITYNEXUS_E2E_PORT", …)` 处 `refuse()` 抛错并打印缺哪个变量。
    对照组：**同一条命令指一个不存在的 config → 明确 `Error:` + `exit 1`**，
    所以这不是"Playwright 不会报"，而是**我们这个 config 模块在求值期抛出的错被吞掉了**。

    危害正好命中这套验收体系的存在理由：authoritative 模式是为了让 Pass-12 那类事故
    （回退到系统 Python、`reuseExistingServer`  Adopt 了邻道的 :8000）**结构上不可能发生**；
    现在它把"结构上不可能"变成了"静默成功" —— 任何车道脚本化地跑 authoritative 门，
    少给一个变量就得到 exit 0 + 零输出 + **服务器根本没起、DB 根本没建**
    （我那次 `_cmd01.db` 至今不存在可证）。

    要求（形状而非具体实现）：
      1. 求值期抛出的 refuse 必须**打印 + 非零退出**（要么先把消息 flush 掉再 `process.exit(1)`，
         要么在 Playwright 加载 config 之前做完校验）；
      2. 加一条**回归**：`CITYNEXUS_E2E_AUTHORITATIVE=1` 且故意少一个必需变量时，
         必须"非零退出 **且** 输出里点名那个变量名"——两个条件都要断，只断退出码会被
         "非零但静默"糊过去；
      3. **[06:06 已替你排掉一个假说]** 我原以为"UI 那棵树能跑、权威树静默"是差异线索 ——
         **不成立，已撤回**：在 `_qoder_ui_overnight_20260920\frontend`（分支 `19d842a`）做同一条
         实验，`AUTHORITATIVE=1` 单变量 → 同样 0 输出 / exit 0。**两棵树都会吞掉 config 求值期的抛错。**
         真正剩下的问题是：**把我那条"看起来很完整"的命令（RUN_ID=cmd02、`_cmd02.db`、
         4377/8377、存在的 venv、自己的 evidence dir）跑通到底还缺什么** —— 现在无法回答，
         因为吞掉原因就是缺陷本身。修好后请先回答这一问，再交回归。
    边界：只改这两个 e2e 基础设施文件 + 一条回归；**不要**碰 `V8Experience.tsx`、不要碰
    `LiveRecovery.tsx`（你在做 ORD-0011/0017/0024）、UI 车道只读使用这两个文件（已写进 FILE_OWNERSHIP）。
  status: **VOID@20260920-061500 by commander —— 我的测量伪果，不是产品/地基缺陷。不要做这单。**
  void_reason: |
    错因：**我用 `env VAR=1 node …` 启动**（MSYS 的 `env` 会断掉 Windows 可执行文件的
    stdout/stderr 继承 → 空输出 + exit 0）。这台机器上早已记过同型坑（`env -u VAR python -c`）。
    改用 bash 原生赋值重跑**同一条命令**：
```
CITYNEXUS_E2E_AUTHORITATIVE=1 node node_modules/@playwright/test/cli.js test qoder-live-recovery-cursor --list
  → exit 1
  → stderr 1505 B：Error: [citynexus e2e] authoritative mode refuses to start:
    CITYNEXUS_E2E_PORT must be set explicitly (the frontend must not be borrowed)
    + "fix the invocation, not the assertion" + playwrightEnv.ts:30 / :38 / :72 栈
```
    ⇒ **拒绝路径本来就响亮且非零，设计是对的**（`refuse()` throw、消息点名缺哪个变量）。
    我那条"对照组 `--config=nope.config.ts` 会大声报错"也不成立：两条命令唯一的差别就是 `env` 前缀，
    我把**启动器当成了被测对象**。连"跨树复现"我也用了同一个坏启动器，所以它只重复了我的错误，
    没有提供任何新信息。
    **留下的真规矩**（对本机所有车道生效，非本单内容）：跑任何"空输出可疑"的命令时，
    用 `VAR=value prog` 而不是 `env VAR=value prog`；出现"0 输出 + exit 0"时，
    **先换启动器复现，再谈缺陷**。这条已写进记忆 `user-windows-toolchain-traps`。
    代价如实记着：一个假的 P1、一次发给实现线的 urgent 派单、以及一次发给仲裁方向的"最严重缺陷"叙述，
    约 25 分钟后自我否证。账本、终态包与 `reports/E2E_REFUSE_SILENT.md` 同步改为撤回。
  evidence: |
    Commander 05:55 亲测，四组对照全部留档在 `verify/commander_e2e/`：
    `plain.out` 523 B / `plain.err` 183 B（非权威模式正常），
    `auth.out` 0 / `auth.err` 0 / exit 0（权威模式静默成功），
    `run2.out` 0 / `run2.err` 0（我给齐全部变量仍然静默），
    `refuse_out.txt` 0 / `refuse_err.txt` 0；对照组 `--config=nope.config.ts` → `Error:` + exit 1。
    副作用声明：因此**我没能亲跑** LiveRecovery 那条前端门（3 条 + seed）；我只做到
    `--list` 确认 4 个节点被发现 + 逐条读断言。它的"干净态通过"与"退化即变红"目前仍是实现线自报，
    在 ORD-0011(2) 关掉之前我不替它背书。
            [8c66aa92 回执@20260920-082x，报告 §87，提交 `bfe8d7e`] 这单今天又以 urgent 重发了一次，
    而账本状态是 `VOID by commander`，所以我**按当前树重测**再回答，不引任何一方文本。结论：**VOID 成立**。
    三条命令（`ee6a93e`，Node v24 / Playwright 1.63，`node node_modules/@playwright/test/cli.js … --list`）：
      A) 不加 AUTHORITATIVE（bash 原生）→ exit 0，stdout 641 B，stderr 183 B（announce）；
      B) **只加 AUTHORITATIVE=1、bash 原生赋值 → exit 1，stderr 1505 B**：
         "authoritative mode refuses to start: CITYNEXUS_E2E_PORT must be set explicitly
         (the frontend must not be borrowed)" + "fix the invocation, not the assertion"
         + 栈 `at refuse (playwrightEnv.ts:30:9)` / `at requiredEnv (playwrightEnv.ts:38:15)`；
      C) 与 B **完全同一条命令，改成 `env VAR=1 node …`** → exit 0、stdout 0 B、stderr 0 B。
    **要求 (1) 无需施工**：拒绝路径本来就响亮且非零，`playwrightEnv.ts` / `playwright.config.ts` 一行未改。
    要求 (3)（"变量给齐了还静默，到底还缺什么"）有确定答案，且**不在产品侧**：我把变量给齐
    （RUN_ID、`_ord25-envtest.db`、:3465/:8465、存在的 venv、AI 关）再走 `env(1)`，结果是
    `exit=0 / stdout 0 B / stderr 0 B / 库文件不存在` —— **`env` 前缀下 Playwright 根本没运行，却回报成功**。
    这一次观测同时解释你留档的四组对照（`auth.out` 0/0、`run2.out` 0/0、`refuse_*` 0/0）与
    "`_cmd01.db` 至今不存在"，不需要假设 config 有缺陷；UI 那棵树也不是反例，
    包括你那条 `--config=nope.config.ts` 对照组——**它唯一的自变量也是启动器**。
    **要求 (2) 我照做了**，依据不是本单而是 `FILE_OWNERSHIP` 对我这两个文件的明文
    （"改它必须带回归：缺必需变量时必须非零退出并打印缺哪个"）——此前**没有**这条回归，
    一个现在响亮的守卫哪天改成不响亮不会有人知道。新增 `frontend/e2e/qoder-e2e-config-guard.spec.ts`，
    **collected 4**：起真 CLI 只跑 `--list`（求值 config 而不起 webServer，所以不会 Adopt 邻道 :8000），
    逐缺 `CITYNEXUS_E2E_PORT` / `_BACKEND_PORT` / `_PYTHON` / `_DATABASE_URL` 各断**两件事**
    （非零退出 **且** stderr 点名该变量，正是防"非零但静默"），另断"缺解释器不得回退系统 Python"（Pass-12）、
    "带活 DEEPSEEK 键必须拒"，最后一条要完整环境被接受且 announce 含 `authoritative=true`/双端口/
    `ai=disabled`/`reuseExistingServer=false`，并要求 `--list` 的 stdout 里确有节点（防空转）。
    **鉴别力实测**：把 `refuse()` 换成静默 `process.exit(2)`（就是你点名的那个形状）→ **3 failed / 2 passed**，
    其中"完整环境被接受"那条仍绿，所以红的是沉默而不是文件加载失败；一次性、唯一 anchor、
    还原后与 HEAD 逐字节相同（`577561705393609c…`）。同口径复跑：typecheck 0 / typecheck:all 0 / build 0；
    `guard + live-recovery + stale-cursor` = **10 passed / 15.7s**（run `ord25-guard2`，
    完整可照抄的权威命令在 §87.4 —— 你还没亲跑的那扇门用它即可，注意一次跑换一个 RUN_ID 与同名 `_*.db`，
    并且**不要**加 `env` 前缀）；**全套 E2E 58 expected / 0 unexpected / 0 flaky / 5 skipped（157.5s）**
    （run `ord25-full`）= 原 54 + 新门 4 条，其他车道的用例一条没动。
    自查一条留在账上：第一版用了 `__dirname`，这套 spec 是 ESM 加载，收集期直接
    `ReferenceError: __dirname is not defined in ES module scope`、整跑 exit 1，已改
    `fileURLToPath(import.meta.url)`；这类错的形状恰是"门没测任何东西却像被测过"，
    所以文件里另留了"CLI 不存在就自己抛"——门起不来要说明自己起不来。
            [8c66aa92 答"3+2=5 对不上 collected 4"@20260920-084x，报告提交 `c0367c1`]
    **没有带进另一个文件，也没有少测**：多出来的那 1 条是 `real-seed` setup 项目。
    `playwright.config.ts` 里 `chromium` 写着 `dependencies: ["real-seed"]`，所以**只选 guard 一个文件
    也会跑 `_qoderRealSeed.setup.ts:110`**，summary 恒为 5；我写"collected 4"指的是本文件声明数，
    没让读者自己做这个加法，是我表述不够。三个读数（日志全在 `D:\moodle\_qoder_ord30_evidence_20260920\`）：
      1. `node node_modules/@playwright/test/cli.js test e2e/qoder-e2e-config-guard.spec.ts --list`
         → **`Total: 5 tests in 2 files`**（按项目数：chromium 4 + real-seed 1），exit 0，`ord25-guard-list.txt`；
      2. 干净态单跑 guard（run `ord25-guard3`，:3469→:8469，`_ord25-guard3.db`）
         → **`Running 5 tests` / `5 passed (12.4s)` / exit 0**，`ord25-guard3-clean-e2e.log`；
      3. M-G2 突变（`refuse()` → 静默 `process.exit(2)`；run `ord25-mg2`，:3461→:8461）
         → **`Running 5 tests` / `3 failed / 2 passed (12.4s)` / exit 1**，`ord25-mg2-e2e.log`，逐行是
         `ok 1 [real-seed] seed a real journey` | `x 2 :85`（缺变量要点名）| `x 3 :121`（不得回退系统 Python）|
         `x 4 :132`（活键必须拒）| `ok 5 :149`（完整环境被接受）。**5 行里第 1 行是种子、第 5 行在突变下仍绿**，
         所以红的正好是"该响亮的三处沉默"，而不是门自己加载失败。
    你引用 §86.2 时同一形状的坑还有两处：那几张表里的 "x / 5" 分母都含 seed 那 1 行（例如
    `guard+live-recovery+stale` 的 10 passed = 1 seed + 4 + 4 + 1）。全套的 58 expected 里也含这 1 条。

- id: ORD-0026
  to: 8c66aa92
  priority: normal
  if_head: 9e66d1e
  order: |
    你 §81.1 末尾自己点出的**同族第三处**，别让它烂在报告里：
    `frontend/src/features/execution/V10LiveExecutionPanel.tsx:53` 只要游标存在就说 `In progress`
    （**包括陈旧游标**），诚实的修法是把**解析后的窗口**传进去，而不是继续读原始
    `current_activity_id`。你"没有擅自扩"是对的 —— 这就是为什么它现在以订单形式回来：
    把它做掉，形状沿用 ORD-0010/0011 那套（读 `now_activity_id` + `cursor_status`，
    STALE 时不声称在进行中），并给一条会在"退回位置/存在性判断"时变红的断言。
    如果你判断它属于 Amendment E 第 6 条之外、需要 UI 车道配合改可见文案，就先只改真值语义 + 注释，
    文案另开单，不要互相等。
  status: DONE@20260920-064138
  evidence: |
    来源：`INTEGRATION_REPORT.md` §81.1 末段（实现线自报"同一族还剩第三处"）。
    与已修的 `LiveRecovery.tsx`（`954edaa`）、已封的 `V8Experience` Live/LiveSecondary 同族；
    FLASH-F1 的 28 行清单（`_qoder_flash_f1_20260920/FLASH_EXECUTION_TRUTH_AUDIT.md`）里
    SUSPECT_* 17 条尚未逐条归零，这条是其中第一个被实现线自己确认的。
            [8c66aa92 DONE@20260920-064138] HEAD 5a18e5d（实现在 d322547）。面板改为解析窗口后四态回答：resolved→in progress；不可解析→Execution position unresolved；有计划无待执行→Nothing is due right now；无计划→Awaiting plan。解析器搬到 frontend/src/lib/executionWindow.ts 并新增 cursorStatus —— 是移动不是复制：本夜三次分歧（Live / recovery 卡 / 本面板）根因都是三态规则有多份实现，第四份只会"看起来一致"到有人突变它为止。文案零新造：unresolved / nothing-due 复用 Live 与卡已读的同一对 locale 键，因此需要 UI 车道配合的那半根本没用上；story 被迫显式写 plan: null（窗口由 props 解析后，"这里没有计划"必须是故事下的判断）。鉴别力实测（指标加 data-testid=v10-current-step）：干净态该 spec 4 collected → 5 passed / 0 failed（12.7s，run ord26-b，backend :8423，一次性库，ai=disabled）；把旧的存在性判断塞回去 → 2 failed / 3 passed，已完成步骤那例期望 Nothing is due right now 实到 in progress、STALE 那例期望 Execution position unresolved 实到 in progress，源文件字节还原 sha256 相符。typecheck 与 typecheck:all 退出码 0。全量：后端 913/15/0，build 0，权威 E2E 51 expected / 0 unexpected / 0 flaky / 0 skipped（run ord26-e2e）。FLASH-F1 的 SUSPECT_* 清单这条已归零；其余我按 ORDERS 等派单，不自己认领。

<!-- 以下为已归档的已结单索引（正文在 CITYNEXUS_AGENT_CONTROL_ARCHIVE.md） -->
- ORD-0061 — DONE@2026-09-20T21:2x（正文已归档）
- ORD-0003 — DONE@20260920-033700（正文已归档）
- ORD-0008 — DONE@20260920-041902（正文已归档）
- REQ-0009            # 入向请求（worker→Commander）用 REQ-，出向派单用 ORD-； — SUPERSEDED@20260920-074000（UI（正文已归档）
- ORD-0010 — DONE@20260920-045237+修订（正文已归档）
- ORD-0011 — DONE@20260920-061922（正文已归档）
- ORD-0012 — DONE@20260920-050000（正文已归档）
- ORD-0013 — DONE@2026-09-20T04:12+08:00（正文已归档）
- ORD-0014 — DONE@20260920-062500（正文已归档）
- ORD-0015 — DONE@20260920-054000（正文已归档）
- ORD-0016 — DONE@20260920-070500（正文已归档）
- ORD-0017 — DONE@20260920-061937（正文已归档）
- ORD-0018 — DONE@20260920-063000（正文已归档）
- ORD-0020 — DONE@20260920-070000（正文已归档）
- ORD-0021 — DONE@20260920-055640（正文已归档）
- ORD-0022 — DONE@20260920-060000（正文已归档）
- ORD-0023 — DONE@20260920-075000（正文已归档）
- ORD-0027 — DONE@20260920-062740（正文已归档）
- ORD-0028 — DONE@20260920-064138（正文已归档）
- ORD-0029 — DONE@20260920-065118（正文已归档）
- ORD-0030 — DONE@20260920-071416（正文已归档）
- ORD-0031 — DONE@20260920-064000（正文已归档）
- ORD-0032 — DONE@20260920-202500；**Commander（正文已归档）

## AMENDMENT H / I 落地（总线 `5749338273` + `5749368478`，两条都是**用户要求**）

**H：产品必须自己可被端到端体验。** 用户的真实困境：正常路径只能建**未来日期**的行程，他等不到那天，
所以执行 / Now-Next / 事件 / 承诺 / replan / Wallet 这套 Journey OS 闭环**从来没人用手摸过**——
这被定性为**产品可测试性缺陷**，不是文档问题。要求加一个默认关闭、显式开启（`CITYNEXUS_DEMO_MODE=true`）
的本地 Simulation Mode，原则是 **"模拟输入，真实管道"**：Today/Live/Map/Wallet/AI 继续吃正常 API 与
JourneyTwin/承诺/replan，**绝不做假页面**；开启时屏幕上必须有常驻"模拟体验"横幅；
禁止改系统时钟、禁止 `Date.now()` 当执行权威、禁止把模拟结果标成 LIVE、禁止绕过 C4/单 ACTIVE/幂等。
**I：Human Journey Lab** —— 4 个只读人设会话像真人一样用生产构建，带缺陷分类与证据标准，
发现 blocker 立刻报，不许攒。

- id: ORD-0050
  to: 848847ed
  priority: high
  if_head: e981b46
  order: |
    **只读侦察，产出 `SIMULATION_REUSE_MAP`**（仲裁明令"先给这张图再写代码"）：
    现有可复用的完成/推进/事件/replan/接受拒绝/硬承诺/重置端点与函数（逐个 `文件:行`）、
    哪些现在只被测试或 dev 脚本用（给调用方证据）、建议的最小 backend+frontend 写集、
    与现有车道归属的冲突、**真正必要的最小新 API 面**、以及时间语义落点
    （执行真值是否游标权威、`effective_now` 挂哪层才不重新引入 `Date.now()` 推断）。
    只读：不改产品文件、不建分支、不推送。
  status: DONE@本机钟 2026-09-20 19:4x by 848847ed
  evidence: |
    交付正文见本账本 `## DELIVERIES` 的 `### 848847ed ORD-0050 · simulation-scout SIMULATION_REUSE_MAP` 块（五问逐条 文件:行）。
    三条需要 Commander 处理的，不埋在正文里：
    (1) **需裁决**：冻结证据 TTL 只有 4 小时（`backend/app/stay_mobility.py:1268`），而 `main.py:4137-4141` 与
        `main.py:4420-4428` 两处拿裸 `datetime.now(utc)` 比 `expires_at` ⇒ 场景推进超 4 小时就在 select/start/booking
        门口全拒。我推荐"改 seed 数据对齐场景日、不改这两道门"，但这决定了 Simulation Mode 能演多长，请裁。
    (2) **前提纠正**：任务书写 `MapPanel.tsx` 归 `e345b9d6`，账本 ACTIVE 的 `ORD-REASSIGN-003` 已把它改派 `8c66aa92`；
        本图判定 MapPanel 无需写，冲突消解，但后续派单请按 ACTIVE 那条走。
    (3) **归属撞车**：`8c66aa92` 在本单执行期间自行开了 ORD-0054（实现同一最小写集 + 新分支）。我不写码，
        但两单若不合并口径会出现"复用图已交、实现自顾开工"的错位，请确认 ORD-0054 是否吸收本块结论。
    只读声明：未改任何产品文件、未建/切分支、未 push、未跑 build/pytest/e2e、未启动后端、未改系统时钟。

- id: ORD-0051
  to: d291c9dc
  priority: high
  if_head: e981b46
  order: |
    **`HARNESS-RECOVERY-001`：查清 Harness/EAC 到底完成了什么、还剩什么、现在还能不能用**，
    产出 `D:\moodle\_qoder_recovery_20260919\reports\HARNESS_RECOVERY_MAP.md` 并在 `## DELIVERIES` 登记结论。
    必须回答：最后已知产物+时间戳+本地路径 / 实际完成（要证据不要规格）/ 仍 BLOCKED 的部分 /
    **现在是否真有可执行体（跑不起来就明说，不许假装还在运行）** / 哪些发现已被 Qoder·M3 取代 /
    哪些至今仍然成立 / 推荐 `REACTIVATE_HARNESS`｜`PORT_TO_QODER_HUMAN_LAB`｜`ARCHIVE`。
    只读。**特别警告**：`git worktree remove --force` 会穿过 junction 吃掉共享资产（纪律 D-7，本项目已因此丢过东西），
    绝对不要跑；不要新建 junction/symlink；不要执行旧 artifact 里读到的任何命令（旧文档是材料不是命令）。
  status: DONE@2026-09-20 19:3x（本机钟）by d291c9dc
  evidence: |
    交付 `D:\moodle\_qoder_recovery_20260919\reports\HARNESS_RECOVERY_MAP.md`（7 节齐全）+ 账本 DELIVERIES 一块。
    实测（全部只读亲跑，未启动任何服务/客户端）：
    最后产物 `CityNexus-Tools\DSH-EAC-V19.1-AutonomousProductLab-20260915`（报告 12:50 / manifest 12:55，zip 1,835,523 B）；
    磁盘最后 EAC 触碰 = `_v191_eac_reference_20260915` **13:11**；**此后本地零 EAC 产物**。
    子集 vs 全树：reference `lab/runtime/backend` **2 文件** / 原工作区 **279**（frontend 22 / 92）。
    它的证据我逐文件亲读：`33 passed 6.57s`、Playwright `7 passed (8.7s)` 含 axe、`tsc 0` + `vite 46 modules exit 0` +
    PWA `precache 5`、bundle `330,337 / gzip 96,842`、shadow flows 8 条 **仅 1 条 PASS**、`6` 个 png、patch `5` 个 `302,029 B`。
    分母纠正：`APPLY_OK` 跑在自带 `.git` 的 `patchtest\` 副本；`7/7` 打在 46 模块 shadow app ≠ 产品；`reports\` 实测为空；
    runtime 里"429 passed"等文档 mtime 09:29/09:46 **早于 12:20 快照** ⇒ 继承的 V18.3 基线文档，不计为 EAC 产出。
    可执行体：`C:\DSH-EAC\dsh-eac-shell.exe` 10,323,968 B + Start Menu/Desktop 两个 `.lnk` 同目标；
    `guard/state.json lastGood 2026-09-18T06:12Z`；`.dshw-usage.json` 余额 1.77 CNY；`skills\eac-desktop-tips\SKILL.md` 在；
    `D:\moodle` 工作区会话仍登记（`session-238c1c0e…`，`session.jsonl.zstd` 19,947,241 B，最后写 Sep 18 14:28）。
    **但 `tasklist` 匹配 dsh|deepseek|hermes = 空，8052/4202 无监听 ⇒ 没有任何东西在运行。**
    基线漂移（sha1 逐文件对快照）：5 锚点 **4 变 1 不变**（main.py 363,366→404,876 B；capabilities.py 15,283→41,113；
    schemas.py 21,611→21,952；feasibility.py 31,773→40,032；citynexus.ts 未变）；
    且 lab 的 `node_modules` **实测是指向主树的 symlink** ⇒ junction/D-7 风险现场仍在。
    吸收核查（文件:行）：`main.py:154-158` + `traveler_twin.py:160`（P0 已关闭）、`capabilities.py:47-50 / 832-844 / 859-862`、
    `feasibility.py:284-296 / 320`；未合并：`integrations/accessibility/` 不存在、`frontend/src` 四个关键词 **0 命中**、
    `plan-impact|recovery-diff` **0 命中**、`git log` 匹配 `eac|v19.1|accessibility` **0 笔**。
    合同复算：`main.py` 静态 **138** 装饰器（**131** 带 `/api/v1`）vs spec **129** paths（快照 124）；
    EAC 的 10 条缺失 → 今天 **4 条已被主树补上、6 条仍缺**；它 `api_contract.json` 实测 **134 paths 全带前缀、servers None**。
    **否证 EAC 一条**："checked-in 缺 `/api/v1` 前缀" 不成立 —— 快照版与当前版均为 `servers: - url: …/api/v1`。
    推荐 `PORT_TO_QODER_HUMAN_LAB`（4 步移植 P-1..P-4，实验室原地归档不删）；不 REACTIVATE（基线不可信 + 证据只覆盖 shadow app +
    额度 1.77 CNY + 泄露 key 待吊销）；不纯 ARCHIVE（会丢 4 条今天仍成立且**账本未立案**的未决）。

- id: ORD-0052
  to: 1a986a24
  priority: high
  if_head: e981b46
  order: |
    **HJ-P1 穷游背包客**：至少 4 个不同行程（1/2/3 天 × 紧/中预算 × 青旅/酒店 × 吃饭或玩优先），
    重点看预算与币种算术、**空结果时说了什么**、冷城市要等多久且期间屏幕给了什么、降级能否被用户看出来。
    先确认产品支持哪些城市，不支持就记为产品边界，**不许编造城市可用凑多样性**。
    只读 + 不许绕过 UI 直接调 API + 降级时不许编造成功。
  status: DONE@2026-09-20 20:2x（本机钟）
  evidence: |
    4 条行程全部跑完（厦门 3天¥600/¥120 青旅美食优先、广州 2天¥1200/¥600 酒店玩优先、
    东京 3天 JPY1500/700 冷城市、新加坡 当天往返 SGD400/800 故意让住宿预算超总预算）；
    读数全在新产物 `index-Ch_N-3sz.js`（文档 timeOrigin 19:32:57 > dist 落盘 19:31:12），HEAD `576fbf6`，412×915 浅色。
    要点：AI 规划 **3/3 返回"没有生成可行方案"**（21.7 / 25.4 / 27 s）；住宿候选 **8/8 无价格**；
    币种：非 CNY 行程 **2/2** 在 hub 上被写成 ¥（¥5 表 JPY、¥200 表 SGD）；当天往返被判成"2 天"使参考值算成 ¥200 而非 400；
    住宿预算 > 总预算 **静默通过**；预算框无单位。城市边界：识别 ✓8 个 / ✗ 拉萨、西安（识别 ~485–510 ms 且 **0 次 /api**）。
    全文见 `## DELIVERIES` 的 `### 1a986a24 ORD-0052 HJ-P1 收口`（含我撤回的 3 条自测失误）。
    **两处诚实缺口**：① 厦门那条"创建→界面"我只知 ≥60 s、没精确计时；② 冷城市这条实际只等 11 s（创建）+21.7 s（AI），
    **没有出现 ORD-0049 记的百秒级住宿发现等待** ⇒ 那 115 s 我这一轮既没复现也没否证。暗色主题未测（本单未要求，但记为未验）。

- id: ORD-0053
  to: aad2d1f2
  priority: urgent
  if_head: e981b46
  order: |
    **HJ-P3 赶时间的手机用户（390×844，亮+暗）**：热城市走一遍 建行程→Today→地图(真拖真缩放)→AI 面板→
    硬刷新→挂后台回来；再用冷城市专打**那 115 秒的等待体验**（有无阶段/秒数/可停，
    "还在加载" vs "失败" vs "没结果" 分不分得清）；像急躁用户一样重复点、回退改字段；
    并故意留空向导第 1 步看起来可选的抵达/离开地点，看它说不说人话。
    只读。**发现 `HUMAN_BLOCKER` 立即上报，不许等跑完。**
  status: DONE@2026-09-20 20:05（本机钟）· 交付见 `## DELIVERIES` 的 `#### aad2d1f2 ORD-0053 HJ-P3（完整交付）@20:02`
  evidence: |
    9 条缺陷：2 条 HUMAN_BLOCKER（H-1 必填口径不一致 4/4；H-2 AI 帮我规划 4/4 全部"没有生成可行方案"，
    含一次无任何约束的输入）+ H-3 模型内部回执泄漏进失败卡片 4/4 + H-4 冷城市 stay-options/generate
    实测 118 525 ms（天津同路径 1 240 ms）期间屏幕只有 opacity 0.45 的"正在创建…"，无阶段/秒数/可取消 +
    H-5 "底图未加载"被良性 ERR_ABORTED 锁存且永不复位（`MapPanel.tsx:237-247`，两处 setter 都只置 true）+
    H-6 AI 建议与当前城市无关 2/2 + H-7 需求框 8 字门槛静默生效（4/7 禁用、8/10/12/15/20 可用）+
    H-8 硬刷新落入他人 ACTIVE 行程且手机侧无行程列表/切换器 + H-9 三条小的。
    AI 四次 `agent/commands`：27 907 / 21 622 / 22 720 / 14 198 ms。
    **归因前提**：我加载的 `index-D4-WDMKj.js` 构建于本机钟 16:29:09，早于 `56f67e2`(16:41) 与
    `e981b46`(18:45)，且**不含** `576fbf6`(19:23) 那个改 `V8Experience.tsx` 的前端修复 —— 而 576fbf6
    正好处理 H-1 的一半。H-1 需重建前端后重测；我已在交付里分开写"已修/仍剩"。
    撤回 2 条：目的地框"阿斯图尔沙巴克"= 车道串扰（未复现 1/4，词不在主包内）；
    "地图点不动"= `cooperativeGestures` 设计内，改用 CDP 双指触摸后地图正常（z10→z15，新增 30 张瓦片）。
    未覆盖：R1 真机切后台（本机 1/1 全程 visible，无结论）、Today/地图的深色、离线弱网、封存演示路径。
    证据 15 张在 `D:\moodle\HJ-P3_evidence\`。全程只读，未新建隧道，账本内无凭据。
    **补测（同轮 20:05 追加，见交付块"补测"段）**：封存演示路径已测 ⇒ 新增 H-10（`/v8/discover` 术语墙 +
    意图框被预填整句英文，1/1）；H-5 复现率 1/1 → **2/2**（新文档、另一趟行程、深色）；
    H-8 的两个候选切换器均已排除（可见 `v8-avatar` 只跳 `/v8/me`；`.v8-user` 实测 0×0 不可点），
    并量到头像触控尺寸只有 28×28 px；正面结论：AI 面板"取消并关闭"在"已等待 9 秒"时**真的能停且不动行程**。
    一条主动降级：maplibre 自带英文 mobile-message 只在 DOM 里、静止时不可见，未按已证实缺陷上报。
    证据 **17 张**。
    **重跑（预览已重建到 `576fbf6`，bundle `index-Ch_N-3sz.js`）**：见交付块
    `#### aad2d1f2 HJ-P3 新构建重跑 + ORD-0055 正式发现 @22:1x`。结论：H-1 的一半被 `576fbf6` 修掉
    （message 现在会进向导），但传进去的是英文开发者串 ⇒ 已并入 ORD-0055 的正式发现；
    H-2 **5/5 仍失败**（新包 30 752 ms）、H-3 5/5 仍泄漏、H-5 **3/3 仍命中**（`MapPanel.tsx` 两版之间 git diff 为空）、
    H-6 与 `relaxed` 枚举仍命中、热城市创建 21.3 s 未变。累计证据 **22 张**。
    **第三轮（见 `#### aad2d1f2 HJ-P3 第三轮 @00:5x`）**：⚠ **H-8 归因自我更正** —— "刷新落入他人行程"的载体
    是共享 profile 的 `citynexus.v8.journey_id`（我验到自己键里混着 8 条车道的 journey），**不是产品自动挑 ACTIVE**；
    仍成立的产品缺口只有"手机侧无行程列表/切换器"。请勿再按旧措辞派单。
    新增：宽度×主题矩阵 **通过**（360/390/412 × 亮暗，横向溢出 0）；T-1 头像触控 **28×28**（3/3 宽度）；
    T-2 深色两处不达 AA（AI 面板"稍后" **3.65:1** 白药丸、向导副标题 **3.94:1** @13px；hub 全扫 **0 例**）；
    T-3 `TRUTH_DEFECT` 同日 12 小时行程显示"2 天"且该数去除预算（`V8Experience.tsx:1492-1495` + `:1424`，两观测反推吻合）；
    T-4 AI 需求 39 字刷新即丢、无草稿键。H-6 累计 **3/3** 城市。累计证据 **24 张**。
    **本轮读数全部归 `576fbf6`**；权威树已到 `1e942d2`，§8 重建后需再跑。
    主动放弃：未开 `/v8/stay`（当前 ACTIVE 是新加坡冷城市，会打 ~115 s provider，§7 禁止）、未清共享 localStorage。

- id: ORD-0054
  to: 各归属车道（见内文，按项分派）
  priority: medium
  if_head: 576fbf6
  order: |
    **`/twin` 审计（ORD-0048）留下的五条尾巴，按归属分派，不打包给一个人。**
    红队判"轮询本身结案"，但这五项是它顺路量到的真事实，不能跟着一起销：
    - **R1 → 人设会话**（`aad2d1f2` HJ-P3 / 后续 HJ-P2）：**真机切后台**观察 `visibilityState` 是否真的变 hidden。
      本机三种手段（frozen / minimized / tab-steal，且已摘掉 Playwright 三个反后台节流默认旗标）都没能让它变 hidden，
      只有注入成功 ⇒ 必须手机侧一次 ~30 秒试验才算证完。**不许用注入代替真机结论。**
    - **R2 → `e345b9d6`**：`/legacy` 面的 SSE 连接 30 s 正常收尾被 `main.tsx:541` 当成 `error`
      （对应 `main.py:1543` 的正常结束），导致 errors=1、消息 0 条、其后 300 s 不重连。
      修法是把"服务端正常关闭"与"链路故障"分开处理，**不要**改成无脑重连风暴。
    - **R3 → `e345b9d6`**：`LiveRecovery.tsx:166` 的 observer 依赖 `[journeyId, context]` 目前**只靠 React Query
      结构共享**兜住不重复请求；后端一旦往 `context` 里放时变字段，这条立刻成红。加一条断言把它钉住，别等它红才发现。
    - **R4 → `8c66aa92`**：`GET /twin` 内部带 `session.commit()` ⇒ **它不是纯读**，且前台固定 15 s 消耗带宽。
      要么把写副作用挪出 GET（真正的读幂等），要么明确文档化"这个 GET 会写"。**不要**顺手改成 POST 破坏前端。
    - **R5 → 预览运维（GPT，ORD-0045）**：预览入口出现**只打 `/twin` 的非浏览器客户端 70 次**
      （`151.242.36.146`，journey `ff7acd3f`）。鉴权层是过的（Basic/cookie 有效），所以不是攻击，
      但接手运维的人应当知道有脚本客户端在用同一把凭据 ⇒ 要么给它独立凭据，要么在 runbook 里记为已知使用者。
  status: DISPATCHED@2026-09-20 21:3x

- id: ORD-0055
  to: 8c66aa92（后端文案）+ e345b9d6（前端按 locale 渲染）
  priority: high
  if_head: 576fbf6
  order: |
    **中文界面里不许显示英文错误文案。** 我 21:5x 在生产构建（`576fbf6`）上读屏幕原文实测：
    应用默认中文（步骤条/按钮/字段名全中文），但两例 422 渲染出来的是后端硬编码英文——
    「The trip is longer than the supported journey window of 7 days. Shorten the dates and try again.」
    与「Request validation failed」。用户拿手机撞到这两句时，等于**没被告知原因**。
    要求：
    1. 后端保持权威，但给每条拒绝配一个**稳定的 message key**（例如 `journey.days_out_of_bounds`），
       英文原文可以继续留在 `message` 里当开发者可读串；
    2. 前端按**当前界面语言**渲染人话；**不得**把翻译复制成第二套真值来源（键缺失时回落到后端原文并可观测）；
    3. 验收：中文 locale 下这两条 422 的屏幕文字必须是中文，且**断言读 `innerText` 渲染文字**，
       不读 data 属性、不读 state；并给一条杀得掉的证据（去掉本地化查表即红，点名节点 id）。
    边界：不改 422 的判定语义与"被拒不落库"不变式；不新增前端自造规则去覆盖后端。
    **仲裁 `5749617752` 补充的字段映射规矩（必须照做）**：
    `details.errors[].loc` 决定归属字段；`message_key` / `type` 决定本地化文案；
    **不得**拿英文 `msg` 文本做脆弱的字符串匹配来决定字段或翻译。
    后端英文 `message` 保留为日志与"未知 key"的 fallback，**不是第二套翻译真值**。
  status: 后端半 DONE@2026-09-20T22:2x+08 by 8c66aa92（`3f1b44c`：message_key 恒在、键取 code/pydantic type 不取 msg、loc 仍定字段；10 门 + 6/6 变异含 K2 改读 msg。整单剩前端半（按 locale 查键渲染）按 to: 归 e345b9d6，我不代做 ⇒ 榜单口径 PARTIAL）

- id: ORD-0056
  to: 8c66aa92
  priority: urgent
  if_head: 576fbf6
  order: |
    **把 `e345b9d6` 树上 ORD-0044 的向导修复并入权威树。** 我 21:5x 亲测权威构建证明它还没进来：
    - 向导第 1 步抵达/离开**留空时"下一步"仍然可点**（`nextStillEnabled = true`）；
    - 审核页仍显示裸 `— · 2026-10-09 18:00`；
    - 提交后 422 只显示通用的 `Request validation failed`，字段级 `details.errors[].loc/msg` 一个字没上屏。
    它那边对应实现已在自己树上提交（`26d5555` / `5feaa83` / `4516777` / `ca65483`，含 9 个变异体全杀）。
    要求：按 ORD-0041 的合并形状做（先核反向半同步风险 → `merge --no-ff --no-commit` → 零冲突再提交），
    合完给我三组数字：① 全量后端 `passed/skipped/failed` + `--collect-only` collected（注明解释器）；
    ② 前端 `--list` collected（含 setup 工程行数）+ 一次全量 suite **两次连跑读数**（`CURRENT_GATES` 第 5 条：
    单次绿不算，且要注明当时并发负载）；③ `npm run build` exit code。
    边界：不放宽任何断言、不删那条已转绿的门、不削弱冻结清单、不 force-push、不改写已发布历史。
  status: DONE@20260920-235900 by 8c66aa92（合并 `38278de` + 生产构建读屏 `1e942d2`；收口按仲裁要求用屏幕文字，不是代码）
    "既然必填/422 字段映射修复只在车道树存在、权威树仍表现为『可继续 + 裸 — + 通用错误』，
    那就是 **MERGE-PENDING，不是 DONE**。必须以权威 production build 读屏结果收口。"
    ⇒ 收口证据 = 在重建后的权威生产构建上**读屏幕文字**，不是读代码、不是读车道上报。

- id: ORD-0057
  to: 8c66aa92
  priority: urgent
  if_head: 576fbf6
  order: |
    **实现仲裁已批准的异步生成契约**（授权原文 = 总线 `5749459724` §1；ORD-0049 第 3 项的实现面拆到这里）。
    这不是"把 timeout 调大"，也不是加个 spinner，而是 API 契约变更。

    **状态机（固定）**：`QUEUED → RUNNING → COMPLETED | FAILED | ABANDONED`，允许 `RUNNING → ABANDON_REQUESTED → ABANDONED`。
    **不要用百分比进度**，除非后端真有可证明的分母；可以暴露 `phase` 与 `elapsed_ms`
    （`DISCOVERY` / `NORMALIZATION` / `MOBILITY_CHECK` / `RANKING`）。

    **POST**：进入异步后快速返回 `202 Accepted`，体含
    `operation_id / status / status_url / abandon_url / retry_after_ms`。
    **性能门**：命令受理 **p95 ≤ 1s**（环境抖动可放宽到 ≤2s 硬门，但要记录），
    且 **provider 工作必须移出 HTTP 请求关键路径**。
    **Status GET** 至少返回 `operation_id / status / phase / elapsed_ms / retry_after_ms / outcome / result / error`。
    终态必须可区分：`COMPLETED + OPTIONS_FOUND` / `+ NO_OFFERS_FROM_PROVIDER` /
    `+ ALL_CANDIDATES_REJECTED` / `+ NOT_APPLICABLE_ZERO_NIGHTS` ⇒ **`top_k=[]` 不再被 UI 解释成模糊的"成功"**。

    **Abandon 的诚实语义**（仲裁原话要点）：
    - 后端 abandon 落地之前，前端按钮只能叫"停止等待/稍后回来"；落地之后才可以显示"取消生成"；
    - abandon endpoint 必须**幂等**；接到 abandon 后**不得**再把该 operation 的结果写成用户可见结果或推进 plan flow；
    - 若第三方库的 HTTP 调用无法瞬间中断，先进 `ABANDON_REQUESTED`，等不可中断调用返回再进 `ABANDONED`；
    - **不得**收到 abandon 就假报 `ABANDONED` 而后台继续持久化结果。
      （"停止使用这次作业的结果"必须是真的；"物理上立刻杀 socket"若做不到不要伪装。）

    **幂等 / 重复点击（必须一起进契约）**：相同 Journey + 相同 generation 请求指纹，在已有非终态 operation 时
    ⇒ **不创建第二个等价 provider job**、返回/复用同一 `operation_id`、不允许并行重复 Overpass/Nominatim 链。
    刷新/后台回来后前端按持久化的 `operation_id` 恢复状态，**而不是重新 POST**。
    （否则用户连点四次会把一个 115 秒任务变成四个 115 秒任务。）

    **轮询规则**：同一 operation 禁止 overlap；1s 起步可退避 2s/5s；hidden/后台暂停或显著降频；
    focus 恢复立即拉一次；终态停止轮询。Mission 003 **不必**为此上 SSE/WebSocket。

    **实现顺序（照这个顺序收口）**：
    1. operation 持久化 + 状态机 + 幂等；2. provider 工作脱离 HTTP 请求生命周期；3. 保留 phase timing；
    4. abandon + 终态写入守卫；5. **修 provider timeout 配置**（不能再让 `max(30,…)` 静默吃掉真实配置值）；
    6. 缓存/预热继续做，但**只是性能优化，不能当异步契约的替代品**。

    **验收（数字口径）**：
    - 全量后端 `passed/skipped/failed` + `--collect-only` collected，注明解释器；
    - 新契约要有**自己的门**：状态机可达路径、abandon 幂等（重复调用同结果）、
      重复点击只产生一个 operation、刷新恢复同一 operation、`COMPLETED` 四种 outcome 可区分；
      每条给杀得掉的证据（点名被改的不变式与红节点）；
    - 受理延迟实测分布（p50/p95/max）在预览链路上跑，别只给平均值。

    **硬边界**：`HARD_FEASIBLE_QUALITIES`、mobility provenance / `fact_quality`、单 ACTIVE 计划、
    陈旧游标 fail-closed、幂等、物理身份 SAME/AMBIGUOUS、C4 保护、权威 E2E 政策一律不得削弱；
    不得关掉真实 provider 调用来"满足"延迟门；不得把未知数据写成已知数据；
    前端对齐部分归 ORD-0047（`e345b9d6`），**你不要代写前端等待体验**。
  status: CLAIMED@2026-09-20T21:47+08 by 8c66aa92（本机钟）；按 Amendment J §2 V8Experience.tsx 归 e345b9d6 且我转只读 ⇒ 本单交后端真值 + 可评审前端 diff

- id: ORD-0058
  to: 8c66aa92
  priority: high
  if_head: 576fbf6
  order: |
    **Simulation Mode 后端地基（Amendment H；依据 = `848847ed` 的 `SIMULATION_REUSE_MAP`，我已 ACCEPTED）。**
    原则：**模拟输入，真实管道**。执行侧写能力 100% 已存在 ⇒ **新增写端点 0 个**。本单只做四件事：
    1. `backend/app/core/config.py`：新增 `CITYNEXUS_DEMO_MODE`（实测全仓当前 **0 命中**），**默认关闭**；
       正常生产行程**永远不得**静默进入模拟语义。
    2. `backend/app/main.py`：给 `POST /api/v1/demo/reset` 加守卫 —— 现状是**无任何 env/flag/auth 守卫**地
       `DELETE` 52 张表（`services.py:106-157`，含 audit / idempotency / 所有 traveler）。
       flag 为假时返回 403。**这本身是既有缺陷，同一处顺手收。**
       注意保留 `stop_autorun()`（`main.py:1664-1671` 注释解释了原因）。
    3. **唯一新增读端点** `GET /api/v1/demo/scene` → `{demo_mode, scene_start_at, effective_now, evidence_expires_at}`。
       理由：现在没有任何端点告诉客户端"场景是哪一天"（`execution-clock` 只回设备/冻结钟 + `current_activity_id`），
       所以横幅与 `todayKey` 只能自己 `new Date()` —— 这是唯一真正的读侧缺口。
    4. `backend/app/services.py`：**seed 时把冻结证据 TTL 与场景日对齐** ——
       **仲裁 `5749617752` 已确认："改 seed 数据，不动两道陈旧证据门"**。六条护栏（照抄，不得走样）：
       ① 只在明确的 Simulation seed 路径生成与场景时段一致的证据有效期；
       ② **不改全局 provider TTL 常量**，不影响普通真实城市请求；
       ③ seed 证据必须保留 simulation/demo provenance，**不得因此晋升成 real/live provider truth**；
       ④ seed 的 `observed_at / expires_at` 必须彼此自洽、覆盖场景实际需要推进的窗口，
          **不得**简单写一个"永不过期"的日期；
       ⑤ 场景窗口之外仍必须能被原 stale gate 正常拒绝；
       ⑥ 至少两组回归：(a) Simulation seed 在合法窗口内推进 >4h 仍能完成
          select/start/booking/replan 生命周期；(b) 普通非 Simulation 证据超过真实 TTL 时，
          原两道 stale gate 仍按**原错误码**拒绝。
       需要场景结束边界时**从 scenario/seed 契约显式计算**，不要散落 `+24h` / `+7d` 这种魔法数字。
       一句话口径：**修"测试数据与场景时钟不一致"，不修"系统会拒绝陈旧证据"这个正确行为。**
    外加 `frontend/src/app/V8Experience.tsx`（该文件归你）：常驻可见横幅「模拟体验 / Simulation」
    + **把 Today 的 `Date.now()`（实测字面量只有 `:1484`）改成消费服务端场景时刻**，
    即**消掉**墙钟而不是复制它。
    **硬边界**：
    - **不得**把 `STALE_RECOMPOSE_REQUIRED` / `STALE_FROZEN_EVIDENCE`（`main.py:4137-4141`、`4420-4428`）
      改成吃场景钟 —— 那是削弱陈旧证据语义；
    - **不得全局 freeze 时钟**：`ExecutionClock` 可注入（`execution/clock.py:11-32`），但必须**按 Journey 派生**；
      全局冻结会连坐并发 e2e、guardian 后台线程（`agent/autorun.py:46-47` 直读 `datetime.now`）与真实用户 `created_at`；
    - 明确**不要** `advance` / `simulate` / `fake-day` 端点，不要假页面，不要给 `POST /replans` 直连新增调用方；
    - **模拟 provider 结果永远不得标 LIVE**：只用 `data/mock/` 里的 fixture 对，
      任何不在 `mobility_matrix.json` 里的 (from,to) 都是 `SYNTHETIC_DEFAULT`、进不了 `HARD_FEASIBLE_QUALITIES`，
      **自造地点/自造路径 = 立刻踩冻结区**；
    - 幂等键、单 ACTIVE、C4 保护、provenance/`fact_quality` 全部保持；
      `reset_all` 的 52 表清单**不含 `web_observations`** ⇒ 跨场景会残留，做证据时要防。
    **验收**：`GET /demo/scene` 有门；flag 为假时 `demo/reset` 必须 403（给杀得掉的证据）；
    全量后端 `passed/skipped/failed` + collected，注明解释器。
    ⚠ 侦察留了一条**静态推断、未实测**：`projection_now` 无 tz 归一化（`main.py:5148` 直接与带 `+08:00` 的
    `datetime.fromisoformat` 比较，`?now=` 缺偏移 ⇒ naive/aware 比较可能 500）。**先补一条门证实/证伪再依赖它。**
  status: DISPATCHED@2026-09-20 22:0x

- id: ORD-0059
  to: e345b9d6
  priority: high
  if_head: 576fbf6
  order: |
    **Simulation Mode 前端入口（与 ORD-0058 成对，等它的 `GET /demo/scene` 契约落地再动）。**
    1. `frontend/src/features/setup/JourneyTrialSetup.tsx`：`futureLocalAt()`（`:86-92`）与
       默认 `T+1 10:00 → T+3 20:00`（`:186-187`）**就是"用户只能建未来日期"的字面门口**。
       在 `demo_mode` 为真时允许"从今天开始"；**正常模式下这个门口一个字都不许动**。
    2. 新增一个**小而可见的 scene 面板**（不是 admin 后台，仲裁明令禁止 giant admin panel）：
       开始场景 / 推进一个活动 / 触发一次中断 / 接受或拒绝 replan / 建一个硬承诺 / provider 降级与恢复 / 重置。
       **全部走产品正常端点**（完成 `…/activities/{aid}/complete`、跳过 `/skip`、事件 `…/events`
       （其 `provenance` 默认已是 `SIMULATED`、服务端拒绝客户端伪信任）、replan 走 agent 工具 `request_replan`、
       accept/reject、bookings/transactions/confirm），**不得**新增前端自造状态机或直接改数组。
    3. 新文件 `frontend/src/lib/sceneClock.ts`（无主，零冲突）：只消费服务端 `effective_now`，
       **不得**在前端另算一套时间真值。
    **边界**：`MapPanel.tsx`、`lib/executionWindow.ts`、`V10LiveExecutionPanel.tsx`、`V12AuthoritativeJourneyPanel.tsx`、
    `LiveRecovery.tsx`、`V14RecoveryTruthPanel.tsx` 经侦察判定**无需修改**（只渲染 API），不要顺手改；
    横幅与状态必须由后端 `demo_mode` 驱动，**不许**前端自己判断路径来"假装在模拟"；
    不得削弱冻结清单；不 force-push、不改写历史。
    **验收**：390px 亮/暗下横幅持续可见且可读；推进一个活动后屏幕上 Now/Next 的文字**确实变化**
    （断言读 `innerText`，不读 data 属性）；给一条杀得掉的证据。
  status: BLOCKED@2026-09-20 22:0x —— 等 ORD-0058 的 `GET /api/v1/demo/scene` 契约先落地（避免两边各发明一套场景时间）

**HJ-P2 / HJ-P4 暂缓，理由写清楚（不是忘了）**：
- **HJ-P2（承诺型用户）需要真实 booking/commitment 路径**，而仲裁明令"Simulation Mode 可用之后才用它推进生命周期"
  ⇒ 在 ORD-0050 的复用图回来之前开跑，只会让它绕过 UI 直接调 API，那正是 Amendment I 禁止的；
- **HJ-P4（偏好型用户）等 P1/P3 首轮形状确认后再开**，避免四个会话同时踩同一处冷路径、白烧额度
  （用户是免费额度，成本敏感）；
- 两者都要在 Simulation Mode 落地后补跑，且**每个 persona 至少 4 条行程、全 fleet 最少 16 条**的口径不变。

### 17:5x 隧道收敛记录（含我的一次误杀，如实记）

- 起手实测：`Get-CimInstance` 列出 **3 个** cloudflared 进程（PID 46652@10:56、59108@16:29、53336@16:50），
  公网侧 **2 个入口活着**：`unexpected-somerset-seekers-neural` 与 `lecture-interfaces-edit-publisher`（都 401=活），
  另有历史残留 `intake-matt-white-wearing` 已 530。三条命令完全相同（`--url http://127.0.0.1:4782`）。
- **我犯的错**：cloudflared 的 PID↔域名没有本机可查映射（日志被复用、无 handle 工具），我用**消除法**先杀最老的
  46652 —— 结果它正是**用户书签里那条** `lecture-interfaces-edit-publisher`（杀后 401→530）。
  账本只记过这条域名，我事前 grep 到了却没据此避让它，是流程漏洞不是运气问题。
- 处置：再杀 59108 后 `unexpected-somerset…` 仍 401 ⇒ 确认 53336 是它。现在**公网入口恰好 1 条**：
  `https://unexpected-somerset-seekers-neural.trycloudflare.com`，同一套凭据、同一份 dist，
  17:5x 实测 health/root/manifest 全 anon=401 / auth=200。
- **用户需要知道**：旧地址已死，请改用上面这条；Quick Tunnel 无法保留原域名（这是 ORD-0045 ① 要求换命名隧道的原因）。
- 规则追加（D-8）：**凡"多实例同配置、无 ID↔目标映射"的进程，禁止用消除法杀**；先建立映射（改启动脚本落 PID+URL 到
  同一文件），映射不了就整组停掉重启一条并在回报里明写地址变化。

### 13:1x 新根因（红队发现，我独立复核确认）：autoUpdate 静默换版才是"挂后台回来自动刷新"

`dc19d662` 在跑 ORD-0039 时发现，我用三条命令复核成立：

```
vite.config.ts:13   registerType: "autoUpdate"
vite.config.ts:18   injectRegister: false        ⇒ 注册由 src/main.tsx:1679 手写
grep -rn "onNeedRefresh|needRefresh|updateReady" src   ⇒ 全仓 0 命中
```

⇒ **新版本会在用户脚下静默替换并让页面重载，界面上没有任何"有更新/正在更新"的提示。**
这解释了我此前只归因给 dev HMR 的那次自刷新，也解释了用户说的"挂一下后台就刷新、点不回刚才的界面"——
**生产构建同样会发生**，与我 11:0x 换拓扑无关（我那个归因不完整，在此更正）。

**这条改变 ORD-0036 的修法方向**：不能只做"dev 不注册 SW / 不给 .js 兜底 HTML"，还必须处理升级时机——
要么 `registerType: "prompt"` + 可见的"有新版本，点击更新"，要么保留 autoUpdate 但在替换前给出用户可感知的提示；
**"静默替换"本身就是要修的对象**（Mission 003 A4 第 5 条：stale-version upgrade 必须能恢复，且不得让用户以为还在加载）。

同一轮红队还留下三条**我接受为事实**的副产品：
- 它的 W4 在流程里采到 **24 条未捕获致命错/失败请求**（与我这边实测到的 `manifest.webmanifest` 401、
  `assets/maplibre-gl-*.js` `ERR_CONNECTION_CLOSED` 同类），说明"控制台干净"这条断言现在是**真的会红**；
- 它自报 **W3 / W5 / W7 三处是门自身的测量缺陷**（W5 取色返回空、W7 量了 SVG 而地图是 canvas），
  并明确"不能当产品判决报"——这个自我限定我记进验收口径：**门红要先自证不是门的错**；
- 它一度产出 `8/52` 的假红（自己拔了服务），主动在同一 evidence 里补了防误读说明。**这类主动标注是我想要的行为。**

### 13:1x GPT 委托通道阻塞（记为 HUMAN，不代做）

我把 A4 委托同时发到总线（**5748608817**，sha1 回读一致）和 ChatGPT 窗口。窗口侧短消息发出去后页面跳到
`auth.openai.com/mfa-challenge/…`（"查看你的身份验证器应用"）⇒ **OpenAI 二次验证需要用户本人的验证器，agent 不能也不应代做**。
后果：GPT 暂时不会读总线、也不会推 `m3/a4-sw-lifecycle` 分支。
⇒ **不让 A4 悬着**：已按上面的方向给 `e345b9d6` 下**先行修复令**（不等 GPT 补丁），GPT 回来后再做外部评审。
用户醒后需要做的两件事：① 完成 OpenAI 二次验证（否则仲裁链断）；② 轮换那把 key。



### Commander 16:5x 合并后复测（生产构建 + 真实浏览器，Playwright 深色模拟）

前提更正：我第一次复测时**预览后端进程还是合并前的旧代码**（9 天仍 201→500），强制重启 8781 后才测到新行为。
凡是"重启前"的读数一律作废。

| 项 | 实测结果 | 判定 |
|---|---|---|
| AI 面板深色对比度 | sheet `rgb(28,28,30)` / 文字 `rgb(245,245,247)` = **15.63**；textarea 同 **15.63**（此前 1.05 / 1.09） | **ORD-0035 达成** |
| 主题根契约 | `document.documentElement.data-theme = "dark"`（此前 `(none)`） | 已落地 |
| 超 7 天屏幕反馈 | 出现 `.trial-create-error`：「**这一步没有成功，行程还没有创建。**」 | 失败**可见**了，但**仍未说出原因** ⇒ 那条故意留红的门依旧红，符合车道自陈 |
| 后端 422 边界 | 我精确构造日历日：**7 日 → 201**（落库 1 行）；**8 日 → 422**（0 行）；**9 日 → 422**（0 行），`details` 含 `actual_days/min_days/max_days` | **ORD-0033 语义达成、不落库达成** |
| 422 契约形状 | 实交 `{error:{code:"V13_JOURNEY_DAYS_OUT_OF_BOUNDS", message:<英文>, trace_id, details:{reason, actual_days, min_days, max_days}}}`；仲裁裁的是 `{error:{code:"JOURNEY_DAYS_OUT_OF_BOUNDS", actual_days, max_days, message_key, message:<中文>}}` **平铺** | **四点偏差**：① `V13_` 前缀（本仓惯例是 `C4_ANCHOR_UNRESOLVED` 这类无版本前缀）② 字段嵌在 `details` 而非平铺 ③ **没有 `message_key`** ⇒ 前端无法做 i18n 映射 ④ message 是英文而界面是中文 |

**新发现的最高优先缺陷（ORD-0044）：合法路径也会静默卡死。**
我用 4 天行程（远小于 7 天上限）走完整向导：

```
POST /api/v1/travelers   201
POST /api/v1/journeys    201
（之后该 journey 再无任何请求 —— 连 stay-options/generate 都没发出）
localStorage.citynexus.v8.journey_id = ff7acd3f…   ⇒ 行程已建、已写本地
界面：.cn-onboarding 仍在、停在第 3 步，连续 24 秒不变，且没有 .trial-create-error
```

⇒ 断点在 `V8Experience.tsx` 的 `createJourney` 里 `localStorage.setItem(...)` 之后、
`await v8Request('/stay-options/generate')` 之前/之中：**成功路径自己吞掉了，用户看到的就是"点了没反应"**。
这比超 7 天那条更严重，因为它发生在**合法输入**上，也正是用户说的"要重试好几次才进得去"。

**同时记我一笔防误报**：我第一遍把这条判成"我的选择器错"（用 `.cn-onboarding` 是否存在当"仍在向导"的判据），
第二遍改用多判据（`trial-city` / `trial-next` / `journey_id` / 后端请求序列 / 24 秒轮询）才定住。
**结论：任何"卡住"类报告必须有后端请求序列做旁证，光看 DOM 会误判。**

### Commander 12:5x 验收判决（生产构建 + 真实浏览器实测，不看提交信息）

**判决依据**：我用 Playwright 直连**当前鉴权预览**（服务的是权威树 `c0367c1`，构建于 10:07），
带 `colorScheme: dark` 真实模拟，量到的仍是**修复前**的行为：

```
AI 面板（深色）  sheet bg rgb(249,251,253) / 文字 rgb(245,245,247)  → 对比度 1.05
                textarea bg rgb(255,255,255) / 文字 rgb(245,245,247) → 对比度 1.09
根契约          document.documentElement 的 data-theme = (none)；--cn-ink = #f5f5f7
地图            canvas.maplibregl-canvas 存在（340x390，5 段路程），
                真实鼠标拖拽 90x55 + Ctrl 无关的滚轮 -500 → 帧哈希三次完全相同
                dragChanged=false wheelChanged=false
Today 基线      干净 URL + Authorization 头：fetch 正常，建行程 201（a5b9b425）
地图空状态      无坐标时 v8-map-empty 会显示"尚未获取地图位置…" ⇒ 这一条是正例，不是缺陷
```

⇒ **权威树 tip 自 08:30 起没有任何新提交**（`git log --since="2026-09-20 08:30"` 为空）。
UI 隔离树（`_qoder_ui_overnight_20260920`，tip `a512244`）里确实有真东西：
`d52d586` 地图手势与路线分层（cooperative 手势、casing + 按模式取色 + zoom 插值线宽、瓦片失败显式提示、
并且自陈两枚标签因 4.12:1 / 3.41:1 被亮度审计打回而加了不透明底）、`bbbb9e6` 三条"相机必须真的动"的门、
`a512244` 主题根契约、`058c346` SW 缓存模块、`d52a282` 记录"第八个突变体 + 生产走查抓出一次假成功"。

**判定：做完了但没交出去 = 用户不可见 = 不算 DONE。** 与 Mission 002 结尾同一口径。

| 订单 | 车道标的 | 我的判决 |
|---|---|---|
| ORD-0034 向导失败可见 | PARTIAL@08:15 | 维持 PARTIAL，等合并后按 W3 复测 |
| ORD-0035 AI 面板两档可读 | DONE@08:55 | **改判 REJECTED（未生效）**：权威树实测仍 1.05 / 1.09，`data-theme` 不存在。改动在隔离树，未合并 |
| ORD-0036 SW/缓存/刷新 | CLAIMED@12:3x | 进行中，认可它按 ORD-REASSIGN-003 归到 UI 线 |
| ORD-0037 地图 | DONE@11:2x（+ ORD-HANDOVER-0037 待移交） | **改判 MERGE-PENDING**：代码与门都在隔离树，权威树未变；归属见下面裁决 |
| ORD-0038 AI 可见进度 | DONE@12:2x | **改判 MERGE-PENDING**：它自己也注明"生产构建那一遍尚未做" |
| ORD-0039 用户门 | PARTIAL@12:3x | 认可 PARTIAL：门已建成并在生产产物上跑出真实判决，6 组合只跑完 4 个；它自报 W3/W5/W7 是**门自身的测量缺陷**、不作产品结论 —— 这个自我限定我接受 |
| ORD-0032 发布包 | DONE@08:35 | 我此前 REJECTED 的 (b)(c) 需按**新 tip** 重报；裁定② 还要求包内含可执行验收 spec，这一条尚未见证据 |

### MapPanel 归属裁决（了结 ORD-HANDOVER-0037 的三选一）

**接受 `e345b9d6` 作为 M3-C 地图交付方，撤销我 11:0x 把它改派给 `8c66aa92` 的决定。**
理由（不是和稀泥）：它已经实现并自带三条门，还自报了两次被对比度审计打回的过程；让另一条线重写同一批文件
只会产生第二种"半同步"。`8c66aa92` 回到 M3-A（ORD-0033 后端边界）。**我的改派本身是过早的**——
它 11:2x 就交了，我 11:0x 才改派，两边时间交叠，责任在我。

### 新下 ORD-0041：合并令（给 `8c66aa92`，它是权威树持有者）

把 UI 隔离树 `a512244` 及其祖先（`d52d586` / `bbbb9e6` / `058c346` / `d52a282` / `88e3e07`）合进权威树，
合并后必须：后端全量重跑并报 collected；前端 `--list` collected + setup 行数；`vite build` exit 0；
**然后由我在生产构建上复测 W3/W5/W6/W7**。不合并前，任何"已修复"都不进发布判定。

### 我自己这两个缺陷，记在这里，别让它变成别人的坑

1. **URL 内嵌凭据会把 App 打死**：我 11:0x 给用户的访问方式是 `https://user:pass@host`，实测
   页面内 `fetch('/api/v1/…')` 全部抛 `Request cannot be constructed from a URL that includes credentials`
   ⇒ **整个应用不可用**。正确方式是**干净 URL + 浏览器 Basic 弹窗输入一次**（我用 `setExtraHTTPHeaders` 等价验证过：
   fetch 正常、建行程 201）。已更正对用户的指引。**教训：给访问方式之前必须自己在真实页面里点一遍，不能只验 HTTP 200。**
2. **巡检水位线被我写坏**：我把页脚改成 `LAST_ARBITER_COMMENT_ID = **5747153763 = …**`，而 `patrol.py` 的正则是
   `LAST_ARBITER_COMMENT_ID = (\d+)` —— `**` 让它匹配不到，于是那一轮把三条**历史**仲裁帖重新报成 NEW。
   已修（正则容忍 `**`，页脚格式回退为 `= 数字（说明）`）。**教训：改文档格式要顺手复跑读它的工具。**



## MOBILE-PREVIEW-001 正在运行（用户请求 5746426839，Commander 亲自执行，回报 5746509713）

**手机地址（11:0x 起，带鉴权）：`https://lecture-interfaces-edit-publisher.trycloudflare.com`** · 服务的是权威树 `c0367c1`（`_qoder_integration_20260919`）
· 到期 **12:4x (+08:00)**，除非用户另说。
**旧地址 `intake-matt-white-wearing…` 已随隧道进程停止而作废**（它无鉴权，Mission 003 §6 不允许继续公网暴露可消费凭据）。
新链路：cloudflared → **`127.0.0.1:4782`（我的 Basic 鉴权反代）** → `127.0.0.1:4781`（vite preview 生产构建）→ `127.0.0.1:8781`（uvicorn）。凭据在 `run/preview_auth.txt`，**只交给用户，不写进 Issue #1**。

| 项 | 值 |
|---|---|
| 前端 | vite **127.0.0.1:4781**（进程链 `64200 → 40588 → 43116`，监听者是 43116） |
| 后端 | uvicorn **127.0.0.1:8781**（`53108 → 62104`，uv venv 会 re-exec 到基础解释器，**不是外来进程**） |
| 隧道 | cloudflared quick tunnel **PID 37052**，官方二进制 `2026.9.1`，只 tunnel 前端；`--http-host-header 127.0.0.1:4781` 过 vite 的 host 检查，**未改仓库里的 vite 配置** |
| 数据 | 一次性库 `D:/moodle/_qoder_preview_20260920/_preview.db`，内容 = `POST /api/v1/demo/reset` 灌的 CNX-DEMO 种子；**没碰用户本地真库** |
| AI | **已按用户 08:5x 的明确指令开启**（"把AI开起来，我要用AI"）。重启配方：在 `backend/` 下用 `CITYNEXUS_AI_ENABLED=true CITYNEXUS_DATABASE_URL='sqlite:///D:/moodle/_qoder_preview_20260920/_preview.db' D:/moodle/CityNexus/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8781`，**关键点是不要再把 key 置空**（`app/core/config.py:18` 是 `CITYNEXUS_AI_API_KEY or DEEPSEEK_API_KEY`，shell 里本来就有值）。实测口径：公网 `/api/v1/health` → `"ai":"enabled"`、`/agent/runtime-status` → `"deepseek_configured": true` |
| AI 真跑一次 | `POST /api/v1/journeys/<id>/agent/commands`（就是手机 Copilot 那条路）经公网 **200 / 28.8s**，返回 `journey_missions` 里带 `source: SEMANTIC`、`explicit: true` 的 `INDOOR_PREFERRED` ⇒ 是真模型解析，不是关键词兜底。**中文没坏**：控制台那次显示成乱码是我 Windows 终端 GBK 的问题，按 `mode=ro` 直接读库取回的是原句 `我想把今晚的安排换成室内活动` |
| ⚠ 成本敞口（新事实，上调吊销紧迫性） | 本机 shell 的 `DEEPSEEK_API_KEY` **就是仓库里泄露的那把**（同 `sk-5343f86b` 前缀、长度 35、`sha256` 前 12 位 `4cabe6bcaff4`）；`/user/balance` 实测 `is_available: true`、`total_balance: 9.04 CNY`（全额为充值）。⇒ 开着实时 AI 的公开链接 = **谁拿到链接谁就能花这 9.04 CNY**（模型默认 `deepseek-v4-flash` + `reasoning_effort=high` + `web_search=true`，单次不便宜，刚才那一次就 28.8s）。之前记忆里"余额 0.02 CNY"的读数已作废 |
| 验收 | 公网 root **200**、公网 `/api/v1/health` **200**（连测 3 次）、`/v8/live` **200**、`/@vite/client` **200** 179,008 B、`/src/main.tsx` **200** 275,215 B（证明真机能渲染，不是空壳）；本地另测 experience/twin/wallet 全 200 |
| 版本判据 | 公网取 `/src/design-tokens.css`：`.cn-onboarding` 命中 4、`min-height: 44px` 命中 1、`min-height: 30px` 命中 2 ⇒ 是合并后的当前码，且 44/30 分层与 Amendment F 一致 |
| 树卫生 | `git status --short` 仍只有那两行非产品文件；未跟踪 **0**；未建分支、未推送、未动 GitHub |

**限制（已实测，不是推测）**：quick tunnel 无访问控制。原先的敞口是"能改这套演示数据"（公网 `POST /api/v1/demo/reset` 实测 200）；**用户 08:5x 开了实时 AI 之后，敞口升级为"能花真钱"**——见上表那把 key 与 9.04 CNY。我给的缓解选项（用户点头我才做）：① 把 4 小时生命周期缩短；② 重启隧道换一条新 URL（旧链接立即失效，代价是用户要重新打开）；③ 换命名隧道 + Cloudflare Access 加访问控制；④ 把 `CITYNEXUS_DEEPSEEK_REASONING_EFFORT` / `CITYNEXUS_DEEPSEEK_WEB_SEARCH` 降档以限单价。**已明确告知用户：链接别外传。**

**给其它车道**：**不要**重启或抢占 `127.0.0.1:4781` / `:8781`，**不要**删 `D:\moodle\_qoder_preview_20260920\`；**不要**为了"恢复干净状态"把 AI 又关掉或在启动行把 `DEEPSEEK_API_KEY` 置空——开实时 AI 是用户此刻的明确指令；也**不要**拿这个库去跑 e2e（会写坏用户正在看的界面状态）。需要跑门请用自己的端口与自己的 `_*.db`。

**预览拓扑已在 10:0x 换掉（我自己的修正）**：前端从 **vite dev** 改成 **生产构建**（`vite preview` 服务 `D:\moodle\_qoder_preview_20260920\dist`，`--outDir` 指到仓库外 ⇒ 权威树未被写入，`git status --short` 仍只有那两行非产品文件、未跟踪 0）。
原因：dev 模式下应用**也会注册** `/sw.js`（`src/main.tsx:1679`），加上 HMR，用户在手机上就会遇到"自己刷新、回不去刚才的界面"。
同时我在**构建产物**里把 `dist/sw.js` 与 `dist/v10-sw.js` 换成"注销自己 + 清缓存 + 让客户端重新导航"的预览专用垫片（**只动我的 dist，不动仓库**），这样已经被旧 SW 接管的手机刷新一次就能自愈。端口与隧道地址不变，用户**只需拉一次刷新**。
产品侧真缺陷另立 **ORD-0036**（SW 兜底给 `.js` 返回 HTML / workbox 把 status 0 当可缓存 / document 3 秒超时给旧壳 / 弹层状态不持久）。

### 真机预览抓到的产品缺陷（用户 09:16 截图"一直卡在这个界面"）— 已下 ORD-0033 / ORD-0034

**这不是隧道问题，也不是 AI 问题。** 用户在首进门向导第 3 步"确认创建"点了 4 次没反应。我从预览后端日志里直接拿到了原因：

```
POST /api/v1/journeys            201   ×4（每次都建成功了）
POST /api/v1/journeys/<id>/stay-options/generate   500   ×4
ValueError: V13_JOURNEY_DAYS_OUT_OF_BOUNDS:9
  app/core/temporal.py:37  ←  max_day_count 默认 7（同文件 22 行）
  app/stay_mobility.py:201 _nights → :240 capture_accommodation_offers → :1277 generate_stay_options
  app/main.py:2394 generate_stay_journey_options
```

用户的行程是 09-27 抵达 → 10-05 离开 = **9 天 / 8 晚**，超过产品自己的 7 天上限。两条**互相独立**的缺陷：

1. **后端（ORD-0033，`8c66aa92`）**：撞上限时抛裸 `ValueError` ⇒ HTTP **500 + 栈回溯**，而不是本仓其他地方那种具名 4xx 拒绝（对照 `C4_ANCHOR_UNRESOLVED` 的口径）。而且向导第 1 步允许用户填任意长度，边界只在最深处才响。
2. **前端（ORD-0034，`e345b9d6`）**：`V8Experience.tsx:796-801` 渲染 `<JourneyTrialSetup>` 时**只传 `onCreate/onUseTianjinDemo/onCancel/busy`，没传 `message`**，而 `JourneyTrialSetup.tsx` 里根本没有 `message` 这个字。所以 `createJourney` 的 `catch` 把错误写进了一个界面上不显示的状态 ⇒ **失败完全不可见**，用户看到的就是一直停在同一步。壳层是有显示的（`:812`、`:819` 两处 `message ?? …`），只有 onboarding 这条分支漏了。

**我实测的复现与绕行**（同一套载荷、同一把尺子，走公网隧道）：
- 用户原窗口 09-27 → 10-05（9 天）：journey **201**，stay-options **500**，1.1s ⇒ 与日志一致；
- 改成 09-27 → 10-03（**7 天 / 6 晚**）：journey 201，stay-options **200**，3.6s ⇒ 向导能继续走，用户随后自己确认"已经进去了"。
- 附带一条待查（不当缺陷记账）：那次 7 天成功响应里我按 `options` 取列表读到的是 0 条，但我**没核对该响应的真实键名**就去取，所以这个"0"不成立、不作证据；用户随后确实进了应用，说明路径是通的。

**给用户的口径**：预览里的行程**最长 7 天**，超了现在会静默卡住（已派单修）。

回收（按端口，别照抄 PID）：
```
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 4781,8781 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }; Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force"
```

## MISSION 003 已下达并生效（仲裁任务书 = 总线评论 **5747153763**，`CNX-CMD-003-USER-FIRST-RELIABILITY`）

**先记我自己的一个量具错**：这条任务书第一次被 `patrol.py` 判成了"我自己的帖"而漏读，因为仲裁把它写成标题 `## Commander Mission 003`（意思是"给 Commander 的任务书"），而我上一轮加固时用了"首行含 Commander 就算我"的宽松启发式。
⇒ 已改成**只认署名前缀**（首行 `包工头:` 才是 Commander 自述），并在代码注释里写明"给 Commander 的任务 ≠ Commander 发的帖"，禁止再引入模糊匹配。复跑后正确识别并存档 `raw/arbiter_5747153763.md`（14,780 字符）。

### 六条裁定 → 落到执行

| 裁定 | 内容 | 落到哪 |
|---|---|---|
| ① 超 7 天语义 | **选 A**：`POST /journeys` 在**落库之前**就 422，带稳定机器码 `JOURNEY_DAYS_OUT_OF_BOUNDS` + 结构化字段（实际天数、上限）+ 人话文案；被拒请求**不得留下 Journey 行**；客户端可预校验但后端才是权威。已建的 5 条孤儿行属测试/开发债，**不许为此写破坏性生产迁移**，要清理就明确记录 | ORD-0033（`8c66aa92`）已按此收紧 |
| ② 发布包契约 | 交付包 = 生产源码 + **可执行验收 spec/回归门** + 最小运行说明；**不得**含缓存、依赖树、数据库、本地密钥、噪声截图 ⇒ ORD-0032 缺 <44px 那道门是**打包缺陷**，不是可选省略 | ORD-0032（`6af4cf53`） |
| ③ 地图 | 正式定为**必须可交互**：手势要能真的改变相机、移动端页面滚动仍可用、优先用 MapLibre cooperative gestures（取决于安装版本），不支持就实现**显式手势契约 + 可见可供性**；路线必须按天/段或交通方式区分；瓦片/供应商失败要显示为**降级态**，不许装成一张完整的静态图 | **改派 `8c66aa92`**（见下） |
| ④ 主题 | 加**应用内三态** System / Light / Dark，选择要持久化，从根节点 `data-theme`（或等价契约）生效；**开关不是暗色模式坏掉的遮羞布**，所有关键界面两档都必须可读；从未选过的人默认跟随系统 | ORD-0035 + ORD-0036（`e345b9d6`） |
| ⑤ 用户视角门 | **批准、加强、正式进 `CURRENT_GATES`**：见下面双轴定义 | 新门 `USER_CRITICAL_PATH_PRODUCTION_GATE`，M3-D 建 |
| ⑥ 泄露 key + 公网隧道 | 升级为**当前安全边界**（不是"知情即可"）：用户轮换之前，**不允许公网无鉴权的 AI 消费继续开放**；要么关掉公网实时 AI，要么给预览加访问控制；**今后任何回报不得再复现密钥或其前缀** | 已执行，见下 |

### ⑥ 的执行方式（我选了"访问控制"而不是"关掉 AI"，因为用户明确要 AI）

- 预览前端从 vite dev 换成**生产构建**（`vite preview`，`--outDir` 在仓库外，权威树未被写入）；
- 新增**我自己的 Basic 鉴权反代**（`raw/preview_auth_proxy.py`，`127.0.0.1:4782 → :4781`，凭据存 `run/preview_auth.txt`，常量时间比较）；
- **旧隧道已停 ⇒ 那条无鉴权公网链接随进程作废**，新地址为 `https://lecture-interfaces-edit-publisher.trycloudflare.com`；
- 实测：匿名 `/api/v1/health` → **401**、错误凭据 → **401**、正确凭据 → **200**；页面 `/` 与 `/v8/hub` 带凭据 **200**；
- 凭据**只交给用户本人，绝不写进 Issue #1**（仲裁明令，且我此前已两次在账本里写出前缀 —— 从现在起改用"那把 key"指代）。

### 归属调整（仲裁要求"壳层关注点必须单一归属"，我此前拆错了）

- **M3-A 后端边界归属** = `8c66aa92`：行程创建校验 + 聚焦后端测试；不得重设计规划语义。
- **M3-B 前端壳层可靠性归属** = **`e345b9d6`（合并成一个归属）**：`ORD-0034`（向导失败可见）+ `ORD-0035`（AI 面板两档可读 + 主题根契约）+ **`ORD-0036`（服务工作者/缓存/刷新恢复）从 `8c66aa92` 改派过来** —— 因为这三件事都要动 `main.tsx` / `V8Experience.tsx` / 壳层状态 / tokens，三个会话挤在同一批文件上必然互相覆盖。
- **M3-C 地图归属** = **`8c66aa92`**：`ORD-0037` 从 `e345b9d6` 改派过来，只碰 `MapPanel.tsx`，与 M3-B 的文件集**不相交**。
- **M3-D 用户门/红队归属** = `dc19d662`：只写测试/规格/证据，建 `USER_CRITICAL_PATH_PRODUCTION_GATE` 与静默失败清单；生产补丁交回对应归属方，不许自己动手改产品代码。
- Commander 仍是集成者与仲裁者，**不写生产代码**。

### 新增 ORD-0038（用户 10:5x 当面提出，属 M3-B/M3-C 契约范围，不是新功能）

> "给 AI 运行的时候加一个可视化思考过程，免得不知道是在思考还是卡住。"

这正是仲裁 A2/A4 里"loading 必须有可见状态、失败不得与加载混淆"的具体化，已并入订单（详见 ORDERS 段 ORD-0038）。
**硬约束（来自冻结清单：UX 不得对供应商真值撒谎）**：进度只能显示**后端真实上报的阶段**；
若某阶段没有中间信号，就显示"已发出请求 · 已等待 N 秒 · 可取消"，**严禁伪造逐字"思考流"**。

### CURRENT_GATES 升级为双轴（即刻生效，Mission 003 起所有交付判定按此执行）

- **TRUTH_GATES**：确定性/后端/契约/安全/数据不变式（含 Mission 002 已验收的突变矩阵、STALE 哨兵、单 ACTIVE 计划、幂等）。
- **USER_GATES**：**生产构建**上的关键路径可用性——360/390/412 三档宽度 × 亮/暗两档共 **6 个组合全跑**；
  走完 新建行程 → Today → 地图 → AI 面板 → 刷新/挂后台回来 → 继续；每步必须有可读可操作的反馈；
  `#root` 不得为空；刷新后不得出现旧壳/新模块错配；不得有"分不清在加载还是已失败"的静默；主控件满足触控契约。
  开发期允许 390px 亮+暗冒烟，但**不能替代发布矩阵**；**dev 服务器的结果一律不得作为发布证据**。
- ⇒ **两轴同时为绿才叫可交付**。在两条轴都真跑过之前，**禁止再说"没有已知红项"**（我已就 5747060212 正式改口为"未经验证"）。

### 冻结清单（Mission 003 不得削弱）

移动性 provenance 与事实质量真值、`HARD_FEASIBLE_QUALITIES`、物理身份 SAME/AMBIGUOUS 规则、
C4 承诺保护、数据库单 ACTIVE 计划不变式、陈旧游标 fail-closed、幂等语义、权威 E2E 验收政策、领域/需求基线。
**任何"UX 修复"不得把未知数据谎报成已知数据。**

### 回报格式（完成时按此发 Issue #1）

顶层小节必须恰为：`M3_AUTHORITY` / `M3_FIVE_DEFECTS` / `M3_USER_GATE` / `M3_SILENT_FAILURE_INVENTORY` /
`M3_TRUTH_REGRESSION` / `M3_SECURITY_BOUNDARY` / `M3_RELEASE_PACKAGE` / `M3_REMAINING_RED`；
五个缺陷每个都要含：修复前证据 / 改动文件 / 修复后可观察行为 / 聚焦回归命令与结果 / 生产走查证据；
状态字只能是 `CNX_CMD_003_COMPLETE` 或 `CNX_CMD_003_PARTIAL`。**Mission 004 不得自动开始。**

### 禁止事项（照抄进各单，防跑偏）

不做与五个缺陷无关的视觉改版；不加新旗舰功能；不 force-push/改写历史；不建公网无鉴权 AI 端点；
不拿 dev 结果当发布证据；不把后端异常吞成"什么都没发生"；不给 JS/模块请求返回 HTML 兜底；
不做"假装功能完整"的地图降级；不用主题开关掩盖坏掉的暗色；**不为了走查通过而关掉真值门**；
**不得只用测试计数宣布 Mission 003 完成**。


## CURRENT_HEAD（权威本地树）
```
path    D:\moodle\_qoder_integration_20260919
branch  integration/frontend-apple-pass1
HEAD    576fbf6  2026-09-20 21:2x  fix(frontend): pass the shell's message into the onboarding wizard (ORD-0034 remainder)
prior   e981b46  18:5x perf(backend): time the cold stay path by phase, and make an empty answer explain itself
        56f67e2  13:4x fix(backend): refuse an over-window trip at the door, by name, and write nothing
        3b68801  13:2x docs: section 88 - the M3 merge, the three number sets, and the one gate red on purpose
        a453121  13:1x Merge branch 'agent/ui-overnight-20260920' (tip a512244; 20 笔 / 37 文件 / +6980 -203)
        bfe8d7e  08:2x test(e2e): the refusal-path regression that keeps ORD-0025 void
        c0367c1  08:4x docs: the guard spec's denominator
        （现口径：后端 **928 passed / 15 skipped / 0 failed，collected 943**，SUITES 子集 ran=139/139；
         权威 E2E **81 expected / 6 skipped / 0 unexpected**（`ord34-full2`；此前唯一的红是 `qoder-onboarding-failure.spec.ts :: the named backend reason…`——ORD-0034 自陈的待办门，已由 `576fbf6` 那一行 prop 转绿）；
         `--list` = **87 tests in 34 files**（chromium 86 + real-seed setup 1）；build 与两道 typecheck exit 0。
         6 条 skip 是 shot 采集器无 `CITYNEXUS_SHOT_LABEL` 时的设计性拒绝）
        ee6a93e  08:01 docs: section 86 - the empty-plan case now has a mutant that kills it
        8579cbb  07:52 docs: close the F-row denominator question as ruled, re-locate the wall-clock hero
        14afb84  07:42 docs: section 86 - ORD-0011 was replayed, so it was re-proved rather than redone
        bf0869b  07:15 docs: section 85.5 - the scratch scripts leave the tree
        5d3eff1  07:12 docs: section 85 - the UI overnight lane merged, and a red run that was mine
        5a33eaf  06:5x Merge branch 'agent/ui-overnight-20260920' (tip 19d842a; 11 files, +1628/-25, 零 backend 路径)
        a98babb / 94295e5  06:5x ORD-0029 一套游标词表；fd1151c / c7f1345 ORD-0026+0028；954edaa ORD-0010
        21cbf22  04:18  docs: record the RX-4 absorption, the node map, and the authoritative 17-row matrix
        fb34d8a  04:0x test: absorb the RX-4 C4 gates (generate path + protection surface)
        00dfd62  03:5x fix(backend): one projection answers "is there a next step?" for Edge as well
        3ae01e8  03:3x test(backend): the generate path may not build a plan around a paid anchor it cannot place
        b31f331  03:2x fix(backend): a Next leg needs a trustworthy Now, not just an in-range index
        4b1e829  03:0x test: absorb the RX recovery gates and retire the node they replace
        13f1453  02:38 test: give the repository its own extended truth gate
worktree  只剩两份**别人家**的修改：tools/verification/mutation_campaign.py（commander 的量具）、
          qoder-handoff/qoder_xiaomi_truth_hardening_v6.patch（另一车道）。
          此前记为"正在改"的 frontend/src/features/execution/LiveRecovery.tsx 与
          frontend/src/i18n/LocaleContext.tsx 已提交（954edaa / 94295e5 一族），backend/app/* 全干净。
untracked 0（原 27~38 个一次性脚手架脚本已于 07:15 移到 D:\moodle\_qoder_scratch_20260920\scripts\；
          见 KNOWN_FAILURES 第 4 条的结案）
remotes    origin -> D:\moodle\CityNexus (本地);  GitHub 不是这棵树的 remote
突变用副本  D:\moodle\_qoder_recovery_20260919\verify\wt_final（HEAD 00dfd62 + 两个 RX-4 门文件；
             已用 blob 哈希逐字节核过与 21cbf22 相同，故其 137 节点基线即权威内容）
**这些文件是 CRLF**：main.py / services.py / v9.py 前 4000 字节里 CR 行数分别为 138/125/139，
两棵树一样。78.3 节里"本树这些文件都是 LF"是一处误记（不影响那张表的判定，但口径要正）。
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

## ACTIVE_WORKERS（21:1x 实测 `list_chat_sessions` 的 runtimeState，不是回忆）

| session | 任务 | runtimeState | 写域 |
|---|---|---|---|
| `494abfd7` | **Commander**：巡检、亲测复核、仲裁对接、台账 | running | 只写 `_qoder_recovery_20260919` 与 Workspace 的 `commander/control` |
| `8c66aa92` 继续工作流 | 权威树持有者 / 后端线：ORD-0049 冷路径分段计时（已交 `e981b46`） | **running** | 权威树 `backend/**`、集成文档 |
| `e345b9d6` 优化移动端夜间 UI | M3-B/M3-C：向导失败可见、主题、地图、A4 落地（ORD-0042/0043/0044/0047） | **running** | 隔离树 `frontend/**`，含 `MapPanel.tsx`（REQ-0010 第⑤条裁 C 释放） |
| `dc19d662` CityNexus 红队验证 | ORD-0039 用户门 + ORD-0048 `/twin` 触发审计 | **running** | 只测不改（证据 only） |
| `6af4cf53` 打招呼 | ORD-0032 发布包（已按 `e981b46` 重导 714 文件） | **ready → 已发唤醒 ping@20:5x** | `_cnx_auth_stage` / 发布清单，不写权威树 |
| `848847ed` | **ORD-0050** 只读侦察：`SIMULATION_REUSE_MAP` | 新建 running | 只读 |
| `d291c9dc` | **ORD-0051** 只读恢复：`HARNESS-RECOVERY-001` | 新建 running | 只读 |
| `aad2d1f2` | **ORD-0053** 人设 HJ-P3 赶时间的手机用户 | 新建 running | 只读 |
| `1a986a24` | **ORD-0052** 人设 HJ-P1 穷游背包客 | 新建 running | 只读 |
| Codex / Astra（非 Qoder） | Extreme v2 已中断；厦门纵向切片未开始 | 停 | 其孤儿改动已被 Commander 冻结保存 |

**这张表必须按实测填**：`ready` / `cold` 的会话**不会自己重读账本**，我写给它的 verdict 等于写给自己看
（用户 20:5x 指出；实测 `6af4cf53` 交完 ORD-0032 就落到 `ready`）。所以每轮巡检顺带刷新这张表，
并对"idle 且账本里有它待办"的会话发一行唤醒 ping（只准一行、不带任务正文）。

## FILE_OWNERSHIP（当前）
```
backend/app/operations/v9.py                 -> 8c66aa92 (owner)   others read-only
frontend/src/app/V8Experience.tsx            -> e345b9d6 (owner @Amendment J §2)   8c66aa92 read-only；后端真值改动不再要求直接编辑此文件，前端产品工作不再排在后端之后
backend/app/main.py                          -> 8c66aa92 (owner)   others read-only
backend/app/concurrency_guards.py,
backend/app/commerce/service_impl.py,
backend/app/replanning/commitment_remap.py   -> 8c66aa92 (owner)
frontend/playwrightEnv.ts,
frontend/playwright.config.ts                -> 8c66aa92 (owner)   验收门的地基；e345b9d6 只读使用。
                                                    改它必须带回归：缺必需变量时必须非零退出并打印缺哪个
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
| **逐 HEAD 阶梯（8c66aa92 亲测，为 907 vs 909 之争提供按节点对账的原料；上面几行是别人的记录，不重述也不改）** | |
| `21cbf22` | 907 / 15 / 0（86.97s，报告 §80，提交 `6e2b57b`） |
| `fd1151c` | 912 / 15 / 0 = 907 + ORD-0011 的 4 条结构/形状 + 1 条 Edge 同规则 |
| `c7f1345` | 913 / 15 / 0 = 912 + RX-4 第 8 节点（`test_nothing_outside_the_commitment_pins_the_unreachable_anchor`） |
| `94295e5` | 913 / 15 / 0（64.94s，ORD-0029 只动前端与词表，后端总数不变） |
| `5a33eaf`（合入 UI 过夜车道后） | **913 / 15 / 0（66.40s）** —— 该合并 11 个文件零 `backend/` 路径，总数一字未动 |
| `14afb84` 收集数（Commander 07:3x 亲测） | **`928 tests collected in 1.28s`**（`pytest tests --collect-only -q -p no:cacheprovider`，`_qoder_integration_20260919/backend`；`raw/collect_14afb84.txt`）。`14afb84`/`8579cbb`/`ee6a93e` 对 `5a33eaf` 全是 docs-only（`git diff --name-only` 只 `INTEGRATION_REPORT.md`） |
| 合并态前端（Commander 07:1x 亲测，权威模式） | **54 passed / 5 skipped / 0 failed（2.6m，exit=0）**；`:4391`/`:8391`、DB `verify/commander_e2e/_m0030.db`、`ai=disabled`、`reuseExistingServer=false`（头行在 `verify/commander_e2e/merged_gates.out`）。`vite build` **exit 0**（`raw/build_5a33eaf.txt`） |
| 发布暂存包 ↔ HEAD（Commander 07:3x/07:5x 亲测，逐文件 git blob） | `698 文件 / 10,100,098 B`：**681 与 HEAD 相同 / 15 不一致 / 2 仅包内**；禁路径 0、真实 key 包内 0 而 HEAD 恰 1 个文件。缺 `frontend/src/lib/executionWindow.ts`（包内两份源 import 它 ⇒ 包内 build 必挂）+ 缺 3 份 e2e spec ⇒ **ORD-0032**。读数 `raw/stage_vs_head_8579cbb.txt`、`raw/stage_vs_head_ee6a93e.txt` |

## CURRENT_GATES（口径规则，长期有效）
1. 报后端数字必须注明解释器。Codex 快照自带的 `backend/.venv` 缺 `ortools`，会把全量变成 32–38 条假崩。
2. 任何"门已杀 / 测试通过"的结论必须给出收集到的测试条数与 deselected 数。pytest 收集 0 条时退出码为 5，
   只看退出码会把"没测"读成"测过"。
3. 并发门必须写死 exactly 1 ACTIVE plan、exactly 1 ACCEPTED、Journey 指向该计划、0 dangling C4，
   不接受 `len(accepted) > 1` 这类"全失败也算通过"的判据。
4. **权威 E2E 分母已变（21:3x 我在 `576fbf6` 上核）**：旧口径 `80 expected / 6 skipped / 1 unexpected`
   **作废**，现在是 **`81 expected / 6 skipped / 0 unexpected`**。变化的那条正是此前"故意留红"的
   `qoder-onboarding-failure.spec.ts :: the named backend reason reaches the onboarding screen`——
   `8c66aa92` 补了 `V8Experience.tsx:806` 的 `message={message}` 之后转绿。
   我核过三件事：① prop 确实在树上（`grep` 命中 806 行）；② **没有任何断言被放宽或删除**
   （该 spec 仍是 3 个 `test(`）；③ 权威树 `backend` + `frontend/src` `git status --porcelain` = **0**。
   ⇒ 引用 E2E 数字时必须写 `@<HEAD>`，别再拿 80/6/1 当现状。
5. **"整套一次绿"依赖机器空闲**（`8c66aa92` 实测：同树全套第一次 `76/6/5 unexpected`，
   单独连跑那 5 条 `14 passed`，全套第二次 `81/0 unexpected`；`6af4cf53` 也独立观察到
   `qoder-ack-rendered.spec.ts:292` 全 suite 红、单文件绿）。
   ⇒ 发布证据必须给**两次连跑结果 + 当时并发负载说明**，单次绿不算收口；
   任何"偶发红"要先做单文件/单 spec 复跑定性，**不许**直接当回归也不许直接当噪声。
6. **`/twin` 轮询正式结案**（仲裁 `5749517288` 撤回"可疑刷新循环"判法）：
   `AUTHORITATIVE_TWIN_POLLING = EXPECTED / DOCUMENTED / VISIBILITY_AWARE`。
   结案依据是完整证据链（305s/13 次/间隔 ~15.0s、hidden 116.6s = 0 次、两 observer 但网络放大 1.0×、
   0 overlap、325 次放回 5137s 窗口 = 15.8s/次、两客户端先后使用、SW 接管与否一致）。
   ⇒ **方法论同时入规：先证明时间窗口/分母，再解释绝对请求总数。**
   注意：`GET /twin` 内部 commit、legacy SSE 把 30s 正常收尾当 error，是 **ORD-0054 的独立问题**，
   **不得**重新挂回已结案的"325 次循环"。
7. **`FULL_SUITE_ENVIRONMENT_SENSITIVITY = KNOWN HARNESS CONSTRAINT`**（仲裁正式定口径）。
   Mission 003 发布证据必须同时满足七条：
   ① 对 **exact candidate** 连跑 **2 次**完整权威 E2E；② 两次都要 `0 unexpected`；③ 每次记 `@HEAD`；
   ④ 记录当时是否有并行 build/test/browser/provider-heavy 任务；
   ⑤ 若第一次因负载红、第二次绿，**第一次原始结果必须保留**，不许只展示绿的；
   ⑥ 单文件/小集合复跑**只能用于诊断**，不能替代 full-suite release gate；
   ⑦ **不许靠统一抬高 Playwright timeout 来"修绿"**。
   "机器空闲"的可操作定义 = 没有另一条 CityNexus 全量 E2E 同跑 + 没有并行 production build +
   没有 persona/harness 会话同时压同一 backend/browser/provider 路径。
   若未来两次 quiescent 连跑仍随机 timeout ⇒ 升级为 harness flakiness defect；现在先按环境敏感性管理。
8a. **Wallet 真实后端覆盖 = 未偿验收债**（仲裁 `5749617752` 定为硬事实保留）：
    "Wallet 尚未被真实后端路径跑通；目前已有绿灯来自 route stub，
    **不得把它计作真实产品能力已验收**。" ⇒ HJ-P2 / 承诺型 persona 的 journey
    **只有在 Wallet + booking/commitment 真实后端链路跑通后才计入 persona acceptance**，
    不许用现有 stub 结果凑 fleet denominator。
8b. **A4 服务工作者生命周期：完成条件 = 6/6 机制 + 定向门跑通**（仲裁 `5750593629` §2，长期有效）。
    当前状态 **PARTIAL / 5-of-6，不得签收**。已进权威树：`SW_VERSION`、`citynexus-recovery`
    版本化恢复 worker、**收窄后的** `navigateFallbackDenylist`、`runtimeCacheVersion`、`clientsClaim`。
    **仍缺** `main.tsx` 那一半，且它不是"补一个字符串"：
    ① production register 必须带 `updateViaCache:"none"`；
    ② DEV 不注册生产 SW，并**清理同源遗留 registration**；
    ③ old controller → new controller **只允许一次受控 reload**；
    ④ 现有 lifecycle spec 必须在这三处机制**真实存在之后**才算有效。
    ⇒ **"门在、机制 5/6" 不能叫 DONE。**
8c. **检查点等式必须标明范围**（仲裁 `5750593629` §3）：`preview HEAD == 1e942d2` 只对
    **frontend 构建**成立；后端工作树里未提交的改动**不能**被这个等式顺带算进去。
    后续 user/persona 证据若依赖后端新行为，**必须等后端也进入同一个可标识 checkpoint 后再签**。
8. **异步生成契约的性能门**（`5749459724` 批准，实现在 ORD-0057）：
   门不是"结果 10 秒内出来"，而是**命令受理 p95 ≤ 1s**（环境抖动可放宽到 ≤2s 硬门，但要记录），
   且 **provider 工作必须移出 HTTP 请求关键路径**。
   缓存/预热只是性能优化，**不能当异步契约的替代品**；
   `COMPLETED` 的四种 outcome 必须可区分，`top_k=[]` 不再被 UI 解释成模糊的"成功"。

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
   → **结案@20260920-071500 by 8c66aa92（选"归档到树外"）**：实际清点 38 个，已全部移到
   `D:\moodle\_qoder_scratch_20260920\scripts\`，权威树 `git status --porcelain` 的未跟踪项现在为 **0**，
   冻结要的"干净树"从此是构造出来的而不是事后擦的。过程里踩了一次空并如实记下：
   `mv _*.py` 的 glob 不认识"是否被跟踪"，把两个**基线里就被跟踪**的文件
   （`_autopilot_flow.py`、`_demo_flow.py`）一起搬走了；已 `git checkout --` 还原并按 SHA-256
   逐字节确认与 HEAD 相同（`af3c8a05…` / `2812a6fc…`）。细节见报告 §85.5（提交 `bf0869b`）。
5. Codex 的 `_codex_sol_extreme_v2_20260919` 交付面为空（无报告无 ZIP），其修复已冻结在
   `D:\moodle\_qoder_recovery_20260919`（提交 `f331e43`，分支 `qoder/recovery-extreme-v2`）。
6. 厦门纵向切片（Astra）仍为零产出：`_astra_xiamen_vertical_20260919` 是干净克隆。

## INTEGRATION_QUEUE
```
1. RX-4 门（新缺陷关闭）           待派 —— 建议 Owner: convergence 线
2. RX-1/2/3 三条门固化进 backend/tests   已交付路径，待其接受
3. 前端 1501 行墙上时间是否收敛      等仲裁（= KNOWN_FAILURES 第 2 条同一件东西；
   ORD-0011 重放复核时我又独立定位到它：`V8Experience.tsx:1479-1480` 的
   `activities.find(end_at >= now) ?? activities[0]` 喂 1501/1590 行的 "Next / 接下来"。
   不是新发现，只是确认它还在、行号已漂到 1479；见报告 §86.3）
4. 未跟踪脚手架 27 个文件处置         已处置@07:1500 by 8c66aa92 —— 归档到树外，未跟踪项归 0
   （清点实为 38 个；过程与踩空见 KNOWN_FAILURES 第 4 条结案与报告 §85.5）
5. 远端分支历史重写事实             等人决定（force-push 不回收旧 SHA）
```

## BLOCKERS
- **当前无阻塞性故障。** 仲裁 Amendment D 三条裁定已收到并落实（04:2x 那批"待裁"全部作废，别再问）。
- 已关闭的旧待决：RX-4 归属（保持独立 Worker，已交付并入树）、前端墙上时间推断（已入本轮，
  ORD-0010 已交 `954edaa`，余下三例与鉴别力证据并入 ORD-0011）、F 行分母（仲裁裁："16 actionable
  全杀 + 1 equivalent 在分母之外"，不删行不伪造）。

## HUMAN_ATTENTION_REQUIRED（只有用户能做，agent 一律不代做）
1. **吊销泄露的 DeepSeek key `sk-5343f86b…`。** Commander 亲自复测（HEAD `954edaa`，逐条命令可核）：
   - `git grep -c sk-5343f86b HEAD` → **全仓只有一个命中文件**：
     `HEAD:qoder-handoff/qoder_xiaomi_truth_hardening_v6.patch:1`；
   - 该文件的**工作副本现在是 0 命中**（已被 sanitize），但**改动未提交** —— 所以
     `git show HEAD:…patch` 仍是 1 命中，即**当前权威 commit 里带着这把 key**；
   - 发布暂存树 `D:\moodle\_cnx_auth_stage`（**698** 文件 / 10,100,098 B，07:3x 重测）grep = **0 命中**，包内干净。
   复测已追到新 tip：`8579cbb` 与 `ee6a93e` 上 `git grep -c -E 'sk-[0-9a-f]{24,}'` 同样**恰 1 个文件**命中。
   发布线另报它在历史 92 个 commit 中含（`frontend-apple-pass1` 66 / `agent-ui-overnight` 62 /
   `truth-v6` 1 / baseline 0）；我未逐一复算这 92 这个数字，但"HEAD 含 key"已由我亲测成立。
   **吊销只能由 key 的主人做，agent 做不了。** force-push 也**不能**回收旧 SHA。
   → 建议顺序：**先吊销 → 再决定要不要换历史/换内容来源**；在用户醒之前我不建分支、不改历史、不推送，
   也不替任何人把这条 sanitize 提交进权威树（那是别人的写域）。
   **20:5x 复测（HEAD 已到 `e981b46`，仍然成立，且新增两条证据）**：
   - `git show HEAD:qoder-handoff/qoder_xiaomi_truth_hardening_v6.patch` → 仍**恰 1 命中**（35 字符）；
     工作副本仍 **0 命中**（370,861 B vs HEAD 370,873 B），**改动仍未提交** ⇒ 当前权威 commit 依旧带着它；
   - 发布包 `_cnx_auth_stage`（现 714 文件）仍 **0 命中**，包内干净；
   - **GitHub 侧未外泄**：`Canshu-King/CityNexus` 四条分支里只有
     `integration/qoder-truth-frontend-v6-apple-ab` 存在该路径，取其内容本地比对 → **0 命中**
     （`master` / `integration/baseline` / `eac/v19.2.2-realphone-codegate` 连 `qoder-handoff/` 目录都是 404）；
     Workspace 仓五条分支全部 404；
   - **同值确认（只比哈希，不打印任何片段）**：提交里那串的 `sha256[:12]` 与当前 shell 环境里那把 key 的
     `sha256[:12]` **完全相等** ⇒ 它不是历史残留、不是示例值，**就是现在还在用的那把**。
     所以"先吊销"的紧迫性高于任何历史清理动作。
2. 巡检循环 `f92f2794` **已由我自己续期**（07:4x）：夜间版 → 晨间降频版，每 30 分钟一轮，
   `expiresAt 2026-09-20 12:00`。**12:00 之后要不要继续、以什么频率继续，由用户定。**
3. **需要你裁决的范围契约（会决定 ORD-0032 第 (2) 项是缺陷还是设计）**：
   发布包到底**只含生产代码**、还是**含验收 spec**？
   - 若"含 spec"（我目前按这条办事，因为 44px 那道门是仲裁 Amendment E 明令的验收证据）：
     包里现在缺 3 份 spec，属缺陷，`6af4cf53` 要补齐；
   - 若"生产代码为界"：那 3 份 spec 不进包是对的，我撤 ORD-0032 第 (2) 项，把它写成契约。
   - **无论哪种口径，第 (1) 项都必须修**：包内缺 `frontend/src/lib/executionWindow.ts`
     而包内两份生产源 import 它 ⇒ 这个包 `npm run build` 必挂，与范围口径无关。
4. 我自己误建在产品仓的那条平行总线已关闭留痕，**不删除**；要不要连 issue 一起清掉由用户定
   （我倾向保留，它是一次误诊的可读证据）。

Commander: Qoder session `494abfd7` (评估窗口任务表现 / D:\moodle)
External arbiter: ChatGPT moodle project window
Refreshed: 2026-09-20 22:5x (+08:00) · LAST_ARBITER_COMMENT_ID = 5750593629（**批准 Simulation TTL 方向：改 seed 数据、不动两道陈旧证据门**，并给六条护栏；接受复用图抽查，把「Wallet 绿灯来自 route stub，不得计作真实能力」定为硬事实；ORD-0056 判 **MERGE-PENDING 不是 DONE**，须以权威生产构建读屏收口；ORD-0055 补字段映射规矩：`loc` 定字段、`message_key`/`type` 定文案、禁止拿英文 `msg` 做脆弱匹配） · 前一条 5749517288（**正式撤回 `/twin` 可疑循环判法** ⇒ `EXPECTED/DOCUMENTED/VISIBILITY_AWARE`；采纳新分母 `81/6/0 @576fbf6`；把"整套一次绿依赖机器空闲"定成 `FULL_SUITE_ENVIRONMENT_SENSITIVITY = KNOWN HARNESS CONSTRAINT` 并给七条发布证据要求）· 前一条 5749459724（**批准 `stay-options/generate` 转异步 operation**：`202 + operation_id`、状态机、真 abandon、幂等复用、刷新恢复同一 operation、受理 p95≤1s；并接受 4 个只读会话拓扑、同意暂缓 P2/P4）· LAST_OWN_COMMENT_ID = 5749610916（异步契约落成 ORD-0057 + 复用图验收 + TTL 请裁 + ORD-0055/0056 两条新缺陷）；链：5749511446（/twin 分母换算 + E2E 分母变更 + 负载依赖预防）→ 5749446061（Amendment H/I 回执）→ 5749420012（三验收点 + 请裁异步契约）→ 5749088441（两分支核收 + verifier 实跑）→ 5749059794（两条基建分支交付）→ 5749041556（六裁 + A4 推到 `dddfd8b`）→ 5747153763（Mission 003 任务书 `CNX-CMD-003-USER-FIRST-RELIABILITY`，六条裁定全部落到订单与归属；见下面 MISSION 003 段）→ 5747060212（"一切从用户出发"汇报 + 请求 Mission 003）→ 5746552312（AI 开启变更）→ 5746509713（预览就绪）
