# CityNexus 试用说明

## 已经启动

- 前端：`http://127.0.0.1:5173/v8/hub`
- 后端：`127.0.0.1:8000`
- 通用城市实时发现：本次启动已启用。
- DeepSeek：本次 Windows 配置未检测到 Key，使用确定性语义回退；不会打印 Key。
- Valhalla live URL：未配置，因此不会声称实时交通。

## 第一次试用自己的城市

1. 打开 `http://127.0.0.1:5173/v8/hub`。
2. 首页右上角点击 `中文`；中文状态会保存，页面语言也会同步。
3. 填写目的城市、国家/地区代码、时区、行程日期、抵达地点、离开地点和预算。
4. 点击 `创建行程`。系统会进入 `城市探索`，非天津行程默认使用 `实时供应商`。
5. 在旅行者意图中描述偏好，例如“喜欢历史文化、少走路、下雨优先室内”。
6. 点击 `探索并组合`。如果 Nominatim/Overpass 不可用，页面会显示不可用或无可行地点；不会把天津演示数据冒充成你的城市。
7. 点击 `旅行票夹`导入火车票、酒店或门票，检查 Journey Memory 和受保护 Commitment。
8. 在 `权威执行` 查看选中的 PlanVersion，在 `实时行程` 和 `地图`查看执行与路线。
9. 在 Journey Hub 点击 `试用其他城市`，可以重新创建另一段行程，不需要改 localStorage。

## 天津完整演示

如果要重复 V14 的完全落地 recovery Golden，在首次页面点击 `使用封存的天津演示`。这是明确标注的 Tianjin sealed replay 路径：它可以验证 grounded PlanVersion、执行、天气/事件恢复、C4 保护、子 PlanVersion、JourneyTwin、地图和离线快照。它不代表其他城市的实时数据。

## 当前限制

- 非天津城市没有本次 V14 的天津 sealed replay，因此依赖已配置的 live Nominatim/Overpass；本次环境中 Fuzhou live discovery 明确返回无可行地点。
- 没有 live Valhalla URL 时，不提供实时交通声明；降级路径必须保持明确标签。
- 通用城市住宿不是完整的 live hotel marketplace；请把住宿结果当作当前支持范围内的捕获/降级数据。
- DeepSeek 未配置时使用 deterministic semantic fallback；配置后才会进行真实模型语义理解。

