# CityNexus — Qoder 集成线交付（truth v6 + 前端 A/B + 真种子 + 视觉验收），2026-09-19

按你 pass-7 给的顺序走完，一条不落：

```
authoritative baseline (380e6ff)
  → v6 truth integration   (b12f24f)  主仓基线上复跑 truth gates
  → frontend/apple-pass1-visual-integration
      group A  (e330ac2)   Apple 视觉 / IA
      group B  (a2124c0)   前置类型 / 行为，逐项 reconcile
  → 真种子 + 可读截图       (cfb2b4a, 1a8462d)
```

先读 `INTEGRATION_REPORT.md`。要点：

- 主仓此前**没有一行源码进过 git**（只有 5 个 9/5 的文档提交）。基线用 `commit-tree` 建立，
  不移动 HEAD、不改工作树，运行中的 `:8000` / `:8011` 后端未受影响。
- v6 与副本逐 blob 等价（副本基线 `c6f9024` 的 40 个源码文件与主仓磁盘 0 处不一致后才搬运）。
  同环境对照：基线 762 passed / 0 failed，+v6 827 passed / 0 failed，NEW = ∅。
- A/B 拆分两块都能 3-way 干净应用，主线代码零降级；`v8Types.ts` 因本仓是 CRLF，
  改为就地插入 2 个字段而不是取 Apple 分支的 LF 整文件（否则 diff 变 46 行重写）。
- 真种子用产品公开 API 建立 SELECTED plan version，15 条 legacy 重新分类：
  8 条是**旧 `/` Journey Mode 界面已被 V8 shell 取代**（规格过期），4 条是 V8 文案/DOM 漂移，
  3 条恢复通过。全量 30/15 → **34 passed / 12 failed**。
- 同一份种子下 truth-only 与 +A/B 对照，差的 1 条是 `v10-accessibility`：
  **Apple 线引入的真实 AA 回归**（`--v8-indigo` 重绑成 #0a66ff，10px 文本在 #f5f5f7 上 4.42:1）。
  深色门抓不到它，因为门只 emulate dark；改成双主题后浅色又一次性暴露 15–48 条/屏，已逐条修完，
  dark 0 / light 0。
- 32 张可读截图（`screens/` 里放 8 张代表，仓库内 `reports/visual-integration/` 是全套）。
  肉眼审查出 7 项只有截图能看见的问题，其中 Today hero 在真实数据下有 4 个 CTA + 2 个语言键，
  说明"≤1 primary CTA"的门只在空分支触发过——**这条线的 positive branch 断言不成立**。
  涉及产品 IA/DOM 决策的，只记录未擅自修。

## 目录

```
INTEGRATION_REPORT.md                       权威报告（分类、数据、待裁决项）
patches/00_cumulative_baseline_to_HEAD.patch  基线 → HEAD 全量
patches/01_truth_v6.patch                     truth v6 落地
patches/02_group_A_visual_ia.patch            A 组
patches/03_group_B_prerequisite.patch         B 组
patches/04_real_seed_and_light_aa.patch       真种子 harness + 浅色 AA 修复
dark-audit-desktop.json / -mobile.json        双主题 × 双视口 0 违规明细
fe_full_seeded.log                            全量 Playwright 原始日志（34/12）
truth_patched.log / truth_baseline.log        后端同环境对照原始日志
screens/                                      8 张代表截图（Today/Live × light/dark × 移桌）
```

## 请裁

1. A/B 整合是否接受，以及接受名。
2. 浅色 AA 修复与双主题门是否作为这条线的正式延续收下。
3. 报告 6.2 的 7 项视觉缺陷归属：哪些进 Apple 下一轮，哪些归主线既有 DOM。
4. 那 8 条 `/` 旧界面 legacy：迁移到 V8 shell 断言，还是标记过期归档。
