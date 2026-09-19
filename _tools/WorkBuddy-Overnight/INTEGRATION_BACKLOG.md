# CityNexus 集成待办事项

## 概述

本文档记录在实现 CityNexus 时需要完成的集成工作。

---

## 架构集成

### 1. Frontend/Backend 集成

**待办：**
- [ ] 实现 Journey 相关的 REST API
- [ ] 实现 PlanVersion 相关的 REST API
- [ ] 实现 ReplanProposal 相关的 REST API
- [ ] 实现 JourneyTwin 读取 API
- [ ] 集成 TanStack Query 进行状态管理
- [ ] 集成 XState 进行状态机管理
- [ ] 集成 Dexie 进行离线缓存

**优先级：** 高

---

### 2. MCP/Agent 集成

**待办：**
- [ ] 设计 MCP tools 权限模型
- [ ] 实现 read-only tools (get_journey, get_plan_version, etc.)
- [ ] 实现 propose tools (generate_replan, etc.)
- [ ] 实现 mutate tools (需要用户授权)
- [ ] 实现 high-risk mutate tools (支付取消等需要额外确认)

**优先级：** 高

---

### 3. Provider 集成

**待办：**
- [ ] 实现 Weather Provider (Open-Meteo)
- [ ] 实现 Transit Provider (Valhalla)
- [ ] 实现 Place Provider (Nominatim, Overpass)
- [ ] 实现 Replay/Frozen Facts 适配器

**优先级：** 中

---

## 数据一致性

### 4. JourneyTwin 一致性

**待办：**
- [ ] 实现 JourneyTwin 刷新触发机制
- [ ] 实现 currentActivityId/nextActivityId 同步逻辑
- [ ] 实现数据一致性验证

**优先级：** 高

---

### 5. PlanVersion 替换

**待办：**
- [ ] 实现 PlanVersion 替换时的 Activity ID 处理
- [ ] 实现 JourneyTwin 更新逻辑
- [ ] 实现前端刷新机制

**优先级：** 高

---

## 事件处理

### 6. Event 处理

**待办：**
- [ ] 实现 Event 去重机制
- [ ] 实现 out-of-order Event 处理
- [ ] 实现 Event 处理状态机

**优先级：** 中

---

### 7. ContextSnapshot 管理

**待办：**
- [ ] 定义数据新鲜度阈值
- [ ] 实现过期数据处理
- [ ] 实现 fallback 机制

**优先级：** 中

---

## 安全性

### 8. 权限控制

**待办：**
- [ ] 实现 Agent 权限边界
- [ ] 实现支付授权
- [ ] 实现高风险操作确认

**优先级：** 高

---

## 测试

### 9. 测试覆盖

**待办：**
- [ ] 实现 Commitment preservation 测试
- [ ] 实现 State transition 测试
- [ ] 实现 Version identity 测试
- [ ] 实现 Provider normalization 测试
- [ ] 实现 Feasibility 测试
- [ ] 实现 Authorization 测试
- [ ] 实现 Frontend refresh 测试
- [ ] 实现 Idempotency 测试

**优先级：** 高

---

## 总结

| 类别 | 待办数量 | 优先级 |
|------|----------|--------|
| 架构集成 | 8 | 高 |
| 数据一致性 | 3 | 高 |
| 事件处理 | 3 | 中 |
| 安全性 | 3 | 高 |
| 测试 | 8 | 高 |
| **总计** | **25** | - |