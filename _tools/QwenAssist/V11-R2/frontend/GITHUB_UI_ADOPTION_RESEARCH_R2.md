# CityNexus — GitHub UI 库采用研究 (R2)

**生成时间**: 2026-09-13  
**研究范围**: 12 个核心 UI 库  
**用途**: 指导组件选型和迁移决策

---

## 执行摘要

| 库名 | 推荐度 | 当前状态 | 行动 |
|------|--------|----------|------|
| shadcn/ui | ✅ 强烈推荐 | 已采用 | 继续使用，补充缺失组件 |
| shadcn/originui | ⚠️ 观察中 | 未采用 | 评估后决定是否替换部分组件 |
| 21st-dev/agent-elements | ⚠️ 需评估 | 未采用 | **许可证已确认：MIT**，可评估使用 |
| 21st-dev/codex-plugin | ⚠️ 需评估 | 未采用 | **许可证已确认：Apache 2.0**，可评估使用 |
| dnd-kit | ✅ 推荐 | 已采用 | 继续使用，补充 Drag & Drop 故事 |
| vaul | ✅ 推荐 | 已采用 | 继续使用 |
| motion-primitives | ✅ 推荐 | 已采用 | 继续使用 |
| magicui | ⚠️ 观察中 | 未采用 | 作为灵感来源，不直接复制 |
| lucide-react | ✅ 强烈推荐 | 已采用 | 继续使用 |
| storybook | ✅ 强烈推荐 | 已采用 | 补充组件状态故事 |
| react-hook-form | ✅ 强烈推荐 | 已采用 | 继续使用 |
| zod | ✅ 强烈推荐 | 已采用 | 继续使用 |
| TanStack Query | ✅ 强烈推荐 | 已采用 | 继续使用，补充查询键规范 |
| TanStack Router | ⚠️ 评估中 | 未采用 | 评估是否从现有路由迁移 |
| otp-ui | ⚠️ 评估中 | 未采用 | 评估后决定是否采用 |

---

## 许可证验证结果 (R2 更新)

### 21st-dev/agent-elements

| 项目 | 内容 |
|------|------|
| **仓库** | https://github.com/21st-dev/agent-elements |
| **许可证** | **MIT** |
| **验证方法** | LICENSE 文件 + README |
| **Copyright** | Copyright (c) 2026 21st.dev |
| **采用决策** | ⚠️ 可评估使用（许可证已明确） |

**注意**: 该库与 21st MCP 绑定，耦合度较高，评估后决定是否采用。

### 21st-dev/codex-plugin

| 项目 | 内容 |
|------|------|
| **仓库** | https://github.com/21st-dev/codex-plugin |
| **许可证** | **Apache License 2.0** |
| **验证方法** | LICENSE 文件 |
| **Copyright** | Copyright 2026 21st.dev |
| **采用决策** | ⚠️ 可评估使用（许可证已明确） |

**注意**: 该库是 Codex 插件，需要 API Key 才能使用。评估是否与项目需求匹配。

---

## 详细分析

### 1. shadcn/ui

**仓库**: https://github.com/shadcn-ui/ui  
**许可证**: MIT  
**当前版本**: 需确认（通过 `package.json` 检查）

**CityNexus 使用情况**:
- 基础组件：Button, Card, Input, Dialog, Sheet, Toast 等
- 表单组件：Form, Select, Checkbox, RadioGroup
- 导航组件：Tabs, Accordion, ScrollArea

**采用决策**: ✅ **继续使用**

---

### 2. shadcn/originui

**仓库**: https://github.com/shadcn/originui  
**许可证**: MIT  

**采用决策**: ⚠️ **观察中**

---

### 3. 21st-dev/agent-elements (R2 更新)

**仓库**: https://github.com/21st-dev/agent-elements  
**许可证**: **MIT** ✅ 已验证

**CityNexus 使用情况**: 无

**风险**:
- 与 21st MCP 绑定，耦合度高
- 需要 API Key

**采用决策**: ⚠️ **可评估使用**
- 许可证已明确，可以安全评估
- 评估与项目的兼容性后再决定

---

### 4. 21st-dev/codex-plugin (R2 更新)

**仓库**: https://github.com/21st-dev/codex-plugin  
**许可证**: **Apache 2.0** ✅ 已验证

**CityNexus 使用情况**: 无

**采用决策**: ⚠️ **可评估使用**
- 许可证已明确，可以安全评估
- 需要 API Key，评估成本后决定

---

### 5. dnd-kit

**仓库**: https://github.com/clauderic/dnd-kit  
**许可证**: MIT  

**采用决策**: ✅ **继续使用**

---

### 6. vaul

**仓库**: https://github.com/emilkowalski/vaul  
**许可证**: MIT  

**采用决策**: ✅ **继续使用**

---

### 7. motion-primitives

**仓库**: https://github.com/ibelick/motion-primitives  
**许可证**: MIT  

**采用决策**: ✅ **继续使用**

---

### 8. magicui

**仓库**: https://github.com/magicuidesign/magicui  
**许可证**: MIT  

**采用决策**: ⚠️ **仅作为灵感**

---

### 9. lucide-react

**仓库**: https://github.com/lucide-icons/lucide  
**许可证**: ISC  

**采用决策**: ✅ **继续使用**

---

### 10. storybook

**仓库**: https://github.com/storybookjs/storybook  
**许可证**: MIT  

**采用决策**: ✅ **继续使用**

---

### 11. react-hook-form

**仓库**: https://github.com/react-hook-form/react-hook-form  
**许可证**: MIT  

**采用决策**: ✅ **继续使用**

---

### 12. zod

**仓库**: https://github.com/colinhacks/zod  
**许可证**: MIT  

**采用决策**: ✅ **继续使用**

---

### 13. TanStack Query

**仓库**: https://github.com/TanStack/query  
**许可证**: MIT  

**采用决策**: ✅ **继续使用**

---

### 14. TanStack Router

**仓库**: https://github.com/TanStack/router  
**许可证**: MIT  

**采用决策**: ⚠️ **评估中**

---

### 15. otp-ui

**仓库**: https://github.com/opentripplanner/otp-ui  
**许可证**: MIT  

**采用决策**: ⚠️ **评估中**

---

## 采用矩阵

| 库名 | 采用状态 | 优先级 | 状态 |
|------|----------|--------|------|
| shadcn/ui | 已采用 | P0 | INSTALLED |
| dnd-kit | 已采用 | P0 | INSTALLED |
| TanStack Query | 已采用 | P0 | INSTALLED |
| 21st-dev/agent-elements | 未采用 | P2 | REFERENCED_ONLY (许可证已明确) |
| 21st-dev/codex-plugin | 未采用 | P2 | REFERENCED_ONLY (许可证已明确) |
| TanStack Router | 评估中 | P2 | NOT_ADOPTED |
| otp-ui | 评估中 | P2 | NOT_ADOPTED |

---

## 下一步行动

1. **P0（本周）**: 补充 Storybook 组件状态故事
2. **P1（下周）**: 制定 TanStack Query 查询键规范
3. **P2（下月）**: 评估 21st-dev 库和 TanStack Router

---

**R2 更新说明**:
- ✅ 已验证 21st-dev/agent-elements 许可证为 MIT
- ✅ 已验证 21st-dev/codex-plugin 许可证为 Apache 2.0
- 更新采用决策为"可评估使用"