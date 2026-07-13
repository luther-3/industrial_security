# PROGRESS.md — 开发进度跟踪

> **最后更新**: 2026-07-13
>
> **当前阶段**: 阶段 1 已完成，准备阶段 2

---

## 进度总览

| 阶段 | 状态 | 开始时间 | 完成时间 |
|------|------|---------|---------|
| 阶段 1: 环境搭建 | ✅ 已完成 | 2026-07-13 | 2026-07-13 |
| 阶段 2: 摄像头连通 | ⬜ 未开始 | — | — |
| 阶段 3: 检测器骨架 | ⬜ 未开始 | — | — |
| 阶段 4: 姿态+摔倒 | ⬜ 未开始 | — | — |
| 阶段 5: 告警音频 | ⬜ 未开始 | — | — |
| 阶段 6: FastAPI 后端 | ⬜ 未开始 | — | — |
| 阶段 7: Vue 前端 | ⬜ 未开始 | — | — |
| 阶段 8: 队友模型接入 | ⬜ 未开始 | — | — |
| 阶段 9: 联调测试 | ⬜ 未开始 | — | — |

**图例**: ⬜ 未开始 | 🔄 进行中 | ✅ 已完成 | ❌ 阻塞

---

## 阶段详情

### 阶段 1: 环境搭建 ✅

**目标**: 创建项目骨架，安装所有依赖，初始化 Git，确认环境可用。

#### 已完成
- [x] 创建完整项目目录结构（engine/, server/, web/, models/, alarms/, data/）
- [x] Python package __init__.py（engine/ + server/）
- [x] 安装 pygame 2.6.1（yolo26_env 唯一缺失的依赖）
- [x] 初始化 Git 仓库 + .gitignore
- [x] 创建 Vue 3 + Vite 项目骨架（npm create vite@latest）
- [x] 安装前端依赖：element-plus, pinia, @element-plus/icons-vue
- [x] 配置 vite.config.js 代理（/stream → localhost:8000, /ws, /api）
- [x] 验证全部 9 个 Python 依赖 import 正常
- [x] Vite 9.1.1 + Node v24.15.0 确认可用

#### 有效
- 全部 Python 依赖在 yolo26_env 中可用：ultralytics 8.4.92 / opencv 4.12.0 / fastapi 0.139.0 / uvicorn 0.51.0 / pygame 2.6.1 / numpy 2.2.6 / websockets 16.1 / torch 2.13.0+cpu / torchvision 0.28.0+cpu
- Vite dev server 可用，proxy 已配置
- Git repo 就绪

#### 坏了
- 无

#### 接下来做什么
- 阶段 2: 摄像头连通

---

### 阶段 2: 摄像头连通 ⬜

**目标**: 通过 OpenCV 从摄像头 MJPEG 地址成功拉流并显示。

#### 已完成
- 无

#### 进行中
- 无

#### 待完成
- [ ] 获取摄像头 IP 地址（需现场确认）
- [ ] 编写 `engine/config.py`
- [ ] 编写 `engine/capture.py` (VideoCapture 类)
- [ ] 编写 `test_camera.py` 并验证拉流成功

---

## 本次会话构建记录

### 2026-07-13 — 规范文档审查修复 (v1.1)

#### 审查来源
另一个 agent 对 6 份规范文档进行了交叉审查。

#### 修复内容

| 问题 | 严重程度 | 修复结果 |
|------|---------|---------|
| 性能目标偏乐观（CPU 双模型 ≥15 FPS 不现实） | 🔴 高 | PRD.md: 下调至 8-15 FPS，增加 4 条 CPU 优化策略 |
| 统计口径不严谨（装备框 ≠ 人数） | 🔴 高 | PRD.md: 增加模型输出契约 3 方案对比，明确要求队友走方案 A |
| 摔倒判断太单一（仅躯干比，弯腰/蹲下误判） | 🟡 中 | PRD.md: 改为多条件 AND（躯干比+宽高比+置信度+时序确认） |
| 告警会抖动（帧级反复开停） | 🟡 中 | PRD.md + APP_FLOW.md: 增加告警状态机（触发3帧/解除5帧迟滞） |
| IMPLEMENTATION_PLAN.md 未完成项标记为 [x] | 🟢 低 | 全部 28 处 [x] 改为 [ ]，与 PROGRESS.md 状态一致 |
| WebSocket 每帧推送没必要 | 🟢 低 | PRD.md: 统计推送改为 5-10 Hz，视频仍按推理帧率 |
| torch 版本可疑 | 🟢 低 | 验证通过：torch 2.13.0+cpu 确认真实存在 |

#### 什么有效
- yolo26_env 中 torch 2.13.0+cpu 真实存在，版本号无误
- 所有 6 处问题已在文档层面修复，等待代码实现验证

#### 什么坏了
- 无（尚未开始编码）

#### 接下来做什么
- 阶段 1: 环境搭建

---

### 2026-07-13 — 规范文档二次审查修复 (v1.2)

#### 审查来源
另一个 agent 对 v1.1 进行交叉审查，发现 PRD 与 BACKEND_STRUCTURE/APP_FLOW 之间存在不一致。

#### 修复内容

| 问题 | 严重程度 | 修复结果 |
|------|---------|---------|
| CLASS_NAMES 仍写旧四类，与方案 A 的 person_* 矛盾 | 🔴 高 | PRD 假设 + BACKEND CLASS_NAMES 统一为 `person_helmet`/`person_no_helmet`/`person_vest`/`person_no_vest`，旧四类标注为兼容方案 |
| BACKEND MJPEG 帧率仍写 15-30 FPS | 🟡 中 | 改为 8-15 FPS，空闲等待从 50ms 改为 100ms |
| BACKEND WebSocket 仍写"推理线程每帧推送" | 🟡 中 | 改为由 server/ws.py 定时器驱动，5-10 Hz |
| BACKEND 摔倒配置仍只有 FALL_TORSO_RATIO | 🟡 中 | 新增 FALL_BBOX_RATIO/TRIGGER_FRAMES/CLEAR_FRAMES/POSE_CONF + STATS_PUSH_INTERVAL + JPEG_QUALITY 共 8 个配置项 |
| BACKEND JPEG 质量 80 vs PRD 60-70 | 🟢 低 | 统一为 JPEG_QUALITY=70 |
| APP_FLOW 摔倒流程缺少迟滞 | 🟡 中 | 加入 3 帧触发/5 帧解除状态机描述，与安全违规流程一致 |

#### 接下来做什么
- 阶段 1: 环境搭建

---

### 2026-07-13 — 规范文档三次审查修复 (v1.3)

#### 审查来源
第三次交叉审查，聚焦前两轮遗漏的尾随引用（PRD 改完但其他文档的引用未同步）。

#### 修复内容

| 问题 | 涉及文件 | 修复 |
|------|---------|------|
| F2 主描述仍是旧四类 | PRD.md | 改为 person_*，显示标签保留 HELMET 等 |
| Detection.class_name 注释仍是旧类名 | BACKEND_STRUCTURE.md | 改为 person_* |
| 摔倒示例代码仍是旧版单条件 | IMPLEMENTATION_PLAN.md | 替换为按 §4.4 接口实现的文字描述 |
| 阶段8 类别名+验证项仍是旧类 | IMPLEMENTATION_PLAN.md | 方案A优先，区分显示标签/内部类别 |
| 检测框颜色表类别名 | FRONTEND_GUIDELINES.md | 内部类别改为 person_*，标签保留 HELMET |
| FPS 示例 24 + 流程类别名 | APP_FLOW.md | FPS→12，类别名同步 |

#### 接下来做什么
- 阶段 1: 环境搭建

---

### 2026-07-13 — 规范文档四次审查修复 (v1.4)

#### 审查来源
第四次审查，指出方案 A（person_* 属性框）与实际队友交付（装备级检测框）不一致，统计会产生重复计数。

#### 实际模型输出（已与队友确认）
队友标注了 4 个装备类：`helmet`/`no-helmet`/`vest`/`no-vest`。同一人可能产生多个装备框。

#### 修复内容

| 问题 | 涉及文件 | 修复 |
|------|---------|------|
| F2 方案 A 的 person_* 属性框假设不成立 | PRD.md | 改为实际装备框模型，新增统计去重规则表（总人数→姿态模型，违规人数→装备框+人体框IoU匹配） |
| CLASS_NAMES 与队友实际输出不一致 | BACKEND_STRUCTURE.md | 恢复为 helmet/no-helmet/vest/no-vest，新增 IOU_MATCH_THRESHOLD=0.3 |
| Detection 类注释 | BACKEND_STRUCTURE.md | 同步为装备框类别名 |
| 检测框颜色表 | FRONTEND_GUIDELINES.md | 改回装备级类别名 |
| 阶段8 模型前提条件 | IMPLEMENTATION_PLAN.md | 改为实际装备框交付物，新增 matching.py 去重模块 |
| 阶段8 验证项缺少去重测试 | IMPLEMENTATION_PLAN.md | 新增组合场景验证（一人多框→不重复计数） |
| 流程中残余类别名 | APP_FLOW.md | 同步类别名 |

#### 接下来做什么
- 阶段 1: 环境搭建

---

### 2026-07-13 — 规范文档 v2.0 — 模型输出契约最终确定

#### 来源
与队友确认标注方案：按人标注，人体级互斥组合框。

#### 最终模型输出
4 个互斥类，每人一个框，框与人 1:1：
- `person_helmet_vest` — 戴帽+穿衣（两项合规 → 绿色框）
- `person_helmet_no_vest` — 戴帽+没穿衣（一项违规 → 橙色框）
- `person_no_helmet_vest` — 没戴帽+穿衣（一项违规 → 橙色框）
- `person_no_helmet_no_vest` — 没戴帽+没穿衣（两项违规 → 红色框）

#### 对软件端的影响（简化）
- ~~`engine/matching.py`~~ — 不需要，删除
- 统计逻辑：总人数 = 框数，违规人数 = 按类别直接加
- 无 IoU 匹配、无去重、无 NMS 聚类

#### 文档变更
- PRD.md F2: 模型契约和统计规则重写
- BACKEND_STRUCTURE.md: CLASS_NAMES 重写，移除 IOU_MATCH_THRESHOLD
- FRONTEND_GUIDELINES.md: 检测框颜色增加橙色（一项违规），更新 4 类标签
- IMPLEMENTATION_PLAN.md: 移除 matching.py，更新阶段 8 验证项

#### 接下来做什么
- 阶段 1: 环境搭建

---

### 2026-07-13 — v2.0 残余引用修复

#### 修复内容

| 问题 | 涉及文件 | 修复 |
|------|---------|------|
| 假设节仍未更新为组合类模型 | PRD.md line 196 | 改为互斥组合类，移除 IoU 去重描述 |
| 流程中仍写 "no-helmet" 装备框 | APP_FLOW.md line 152 | 改为 person_no_helmet_vest / person_no_helmet_no_vest |
| JSON 示例字段名不一致 (total vs total_persons) | APP_FLOW.md line 175 | 统一为 total_persons |
| 阶段 9 违规预期仍写红色框 | IMPLEMENTATION_PLAN.md line 435 | 改为单项橙色/双项红色 |
| 示例 FPS 值 24.5 与目标 8-15 不一致 | BACKEND_STRUCTURE.md ×2 + APP_FLOW.md ×1 | 改为 12.0 |

#### 接下来做什么
- 阶段 1: 环境搭建

---

## 阻塞问题

| 编号 | 问题 | 影响阶段 | 状态 |
|------|------|---------|------|
| B1 | 摄像头具体 IP 地址未知 | 阶段 2, 9 | 🔴 等待现场确认 |
| B2 | 队友模型 helmet_vest.pt 未交付 | 阶段 8 | 🟡 不影响前期开发（有占位模型） |
| B3 | 告警音频文件未准备 | 阶段 5 | 🟡 可先用测试音频或临时生成 |

---

## Git 提交记录

| 提交 | 日期 | 描述 |
|------|------|------|
| (首次提交) | — | 待完成阶段 1 后提交 |
