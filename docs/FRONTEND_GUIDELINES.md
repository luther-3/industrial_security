# FRONTEND_GUIDELINES.md — 前端设计系统规范

## 1. 设计理念

### 1.1 总体原则
- **清晰优先**: 数据可读性第一，装饰第二
- **信息层级**: 视频 > 告警统计 > 系统信息
- **克制配色**: 日常浅色管理风，告警状态用红色点缀
- **即时反馈**: 告警状态变化需立即视觉响应（颜色切换 + 动画）

### 1.2 参考风格
- 企业级后台管理系统（类似若依 / Vue Admin Template 的浅色风格）
- 监控室仪表盘的告警态设计
- Element Plus 默认浅色主题为基础

---

## 2. 色彩系统

### 2.1 基础色板

| Token | 色值 | 用途 |
|-------|------|------|
| `--bg-page` | `#F0F2F5` | 页面背景 |
| `--bg-panel` | `#FFFFFF` | 卡片/面板背景 |
| `--bg-sidebar` | `#FFFFFF` | 侧边栏背景（本项目无侧边栏） |
| `--border-default` | `#DCDFE6` | 默认边框 |
| `--border-light` | `#E4E7ED` | 浅色边框 |
| `--text-primary` | `#303133` | 主要文字 |
| `--text-regular` | `#606266` | 常规文字 |
| `--text-secondary` | `#909399` | 次要文字 |
| `--text-placeholder` | `#C0C4CC` | 占位文字 |

### 2.2 功能色

| Token | 色值 | 用途 |
|-------|------|------|
| `--color-primary` | `#409EFF` | 主色（Element Plus 默认蓝） |
| `--color-success` | `#67C23A` | 正常/安全（佩戴安全帽、穿反光衣） |
| `--color-warning` | `#E6A23C` | 警告（注意） |
| `--color-danger` | `#F56C6C` | 危险/违规（未戴安全帽、未穿反光衣、摔倒） |
| `--color-info` | `#909399` | 信息（中性） |

### 2.3 告警态专用色

| Token | 色值 | 用途 |
|-------|------|------|
| `--alert-bg` | `#FEF0F0` | 告警卡片背景（淡红） |
| `--alert-border` | `#F56C6C` | 告警卡片边框 |
| `--alert-text` | `#F56C6C` | 告警文字色 |
| `--alert-overlay-bg` | `rgba(245, 108, 108, 0.15)` | 摔倒警告叠加层背景 |
| `--alert-overlay-text` | `#F56C6C` | 摔倒警告叠加层文字 |

### 2.4 检测框颜色（视频画面标注）

| 类别 | 边框色 (BGR for OpenCV) | 标签文字 |
|------|--------------------------|---------|
| `helmet` (佩戴安全帽) | `(103, 194, 58)` #67C23A 绿色 | HELMET |
| `no-helmet` (未佩戴) | `(108, 108, 245)` #F56C6C 红色 | NO-HELMET |
| `vest` (穿反光衣) | `(103, 194, 58)` #67C23A 绿色 | VEST |
| `no-vest` (未穿) | `(108, 108, 245)` #F56C6C 红色 | NO-VEST |

---

## 3. 字体系统

### 3.1 字体族

```css
font-family:
  -apple-system,
  BlinkMacSystemFont,
  "Segoe UI",
  "PingFang SC",
  "Microsoft YaHei",
  "Helvetica Neue",
  Arial,
  sans-serif;
```

### 3.2 字号阶梯

| 用途 | 字号 | 字重 | 行高 |
|------|------|------|------|
| 页面标题 | `20px` | `600` | `28px` |
| 统计数字 | `48px` | `700` (DIN 风格等宽更好) | `1.2` |
| 统计标签 | `14px` | `400` | `22px` |
| 状态标签 | `12px` | `500` | `20px` |
| 告警大字 | `36px` | `700` | `1.4` |
| 系统信息 | `12px` | `400` | `20px` |
| 底部状态栏 | `12px` | `400` | `20px` |

### 3.3 数字字体（统计面板专用）

统计面板的大数字优先使用等宽/技术风格字体，如果系统不支持则 fallback：

```css
.stat-number {
  font-family: "SF Mono", "Menlo", "Consolas", "Courier New", monospace;
  font-size: 48px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;  /* 等宽数字，防止跳动 */
}
```

---

## 4. 间距系统

基于 4px 基准网格：

| Token | 值 | 用途 |
|-------|-----|------|
| `--spacing-xs` | `4px` | 紧凑元素间距 |
| `--spacing-sm` | `8px` | 图标与文字间距 |
| `--spacing-md` | `16px` | 卡片内边距、组件间距 |
| `--spacing-lg` | `24px` | 区块间距 |
| `--spacing-xl` | `32px` | 页面级间距 |

---

## 5. 组件规范

### 5.1 页面布局

```css
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--bg-page);
}

.main-content {
  display: flex;
  flex: 1;
  padding: 24px;
  gap: 24px;
}

.video-section {
  flex: 0 0 65%;
  max-width: 65%;
}

.stats-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
```

### 5.2 顶部导航栏 (TopNavBar)

```
高度: 56px
背景: #FFFFFF
下边框: 1px solid #E4E7ED
```

```css
.top-nav {
  height: 56px;
  background: #FFFFFF;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.top-nav .title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.top-nav .status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.top-nav .status-dot.running { background: #67C23A; }
.top-nav .status-dot.alarming { background: #F56C6C; animation: pulse 1s infinite; }
```

### 5.3 统计卡片 (StatCard)

```css
.stat-card {
  background: #FFFFFF;
  border-radius: 8px;
  border: 1px solid var(--border-light);
  padding: 20px;
  transition: border-color 0.3s, background-color 0.3s;
}

/* 正常态 */
.stat-card.normal {
  border-color: var(--border-light);
}

/* 告警态 */
.stat-card.alert {
  border-color: var(--alert-border);
  background-color: var(--alert-bg);
}

.stat-card .label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.stat-card .value {
  font-size: 48px;
  font-weight: 700;
  font-family: "SF Mono", "Menlo", "Consolas", monospace;
}

.stat-card.normal .value {
  color: var(--color-success);  /* 0 → 绿色 */
}

.stat-card.alert .value {
  color: var(--color-danger);   /* > 0 → 红色 */
}
```

**卡片规格:**
- 最小高度: 120px
- 圆角: 8px
- 阴影: 无（扁平风格）
- 告警态过渡动画: `transition: all 0.3s ease`

### 5.4 视频监控区 (VideoMonitor)

```css
.video-container {
  position: relative;
  background: #000000;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border-light);
}

.video-container img {
  width: 100%;
  height: auto;
  display: block;
}
```

- MJPEG 视频通过 `<img>` 标签加载
- 背景为纯黑 `#000000`
- 视频比例: 由摄像头输出决定（典型 4:3 或 16:9）
- 摔倒告警叠加层绝对定位于视频区域中心

### 5.5 告警叠加层 (AlertOverlay)

```css
.alert-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(245, 108, 108, 0.12);
  border: 3px solid #F56C6C;
  border-radius: 12px;
  padding: 24px 48px;
  pointer-events: none;  /* 不阻挡视频点击 */
}

.alert-overlay .text {
  font-size: 36px;
  font-weight: 700;
  color: #F56C6C;
  text-shadow: 0 0 20px rgba(245, 108, 108, 0.5);
  animation: alert-blink 0.8s ease-in-out infinite;
}
```

### 5.6 底部状态栏 (BottomStatusBar)

```
高度: 32px
背景: #FFFFFF
上边框: 1px solid #E4E7ED
```

```css
.bottom-bar {
  height: 32px;
  background: #FFFFFF;
  border-top: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  font-size: 12px;
  color: var(--text-secondary);
}
```

---

## 6. 动画规范

### 6.1 告警闪烁

```css
@keyframes alert-blink {
  0%, 100% { opacity: 1.0; }
  50%      { opacity: 0.3; }
}

@keyframes pulse {
  0%, 100% { transform: scale(1.0); opacity: 1.0; }
  50%      { transform: scale(1.3); opacity: 0.6; }
}
```

### 6.2 过渡曲线

| 场景 | 时长 | 曲线 |
|------|------|------|
| 卡片状态切换 | `300ms` | `ease` |
| 告警叠加出现/消失 | `200ms` | `ease-in-out` |
| 数字变化 | 瞬间（无动画，防止误导） |
| 状态灯脉冲 | `1s` 无限循环 | `ease-in-out` |

### 6.3 告警叠加层出现/消失

```css
/* 出现 */
.alert-overlay.enter {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.9);
}
.alert-overlay.enter-active {
  opacity: 1;
  transform: translate(-50%, -50%) scale(1);
  transition: all 200ms ease-in-out;
}

/* 消失 */
.alert-overlay.leave-active {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.9);
  transition: all 200ms ease-in-out;
}
```

---

## 7. 响应式布局

### 7.1 断点

| 断点 | 宽度 | 布局 |
|------|------|------|
| 桌面 (默认) | ≥ 1280px | 视频 65% + 统计面板 35% 左右布局 |
| 小屏 | < 1280px | 视频 + 统计面板上下堆叠 |

### 7.2 小屏适配

```css
@media (max-width: 1279px) {
  .main-content {
    flex-direction: column;
  }
  .video-section {
    flex: none;
    max-width: 100%;
  }
  .stats-section {
    flex-direction: row;
    flex-wrap: wrap;
  }
  .stat-card {
    flex: 1;
    min-width: 200px;
  }
}
```

---

## 8. 图标规范

| 场景 | Element Plus 图标 | 说明 |
|------|-------------------|------|
| 系统标题 | `<Monitor />` | 监控图标 |
| 总人数 | `<User />` | 用户图标 |
| 未戴安全帽 | `<Warning />` | 警告三角 |
| 未穿反光衣 | `<Warning />` | 警告三角 |
| 摔倒 | `<Bell />` | 警铃 |
| 系统状态（运行中）| `<CircleCheck />` | 绿色对勾 |
| 系统状态（告警中）| `<CircleClose />` | 红色叉 |
| FPS 显示 | `<Odometer />` | 仪表 |
| 摄像头状态 | `<VideoCamera />` | 摄像头 |

---

## 9. 前端项目结构

```
web/
├── index.html                       # HTML 入口
├── package.json                     # 依赖配置
├── vite.config.js                   # Vite 构建配置
└── src/
    ├── main.js                      # Vue 应用入口
    ├── App.vue                      # 根组件（布局）
    ├── components/
    │   ├── TopNavBar.vue            # 顶部导航栏
    │   ├── VideoMonitor.vue         # 视频监控区
    │   ├── AlertOverlay.vue         # 摔倒告警叠加层
    │   ├── StatsPanel.vue           # 统计面板容器
    │   ├── StatCard.vue             # 单个统计卡片
    │   ├── SystemInfo.vue           # 系统运行信息
    │   └── BottomStatusBar.vue      # 底部状态栏
    ├── composables/
    │   └── useWebSocket.js          # WebSocket 连接 Hook
    └── stores/
        └── monitor.js               # Pinia 状态 (stats)
```

---

## 10. Element Plus 覆盖

本项目基于 Element Plus 默认浅色主题，按需覆盖以下变量：

```scss
// 不需要覆盖 — 完全使用 Element Plus 默认浅色主题
// 仅添加项目专用的 CSS 变量（见上文色彩系统）
// Element Plus 组件直接使用，不做全局样式覆盖
```

**使用的 Element Plus 组件清单：**

| 组件 | 用途 |
|------|------|
| `el-card` | 统计卡片外壳（或自定义 StatCard） |
| `el-tag` | 系统状态标签 |
| `el-icon` | 图标展示 |
| `el-divider` | 分隔线 |
| `el-progress` | （可选）FPS 仪表显示 |

---

## 11. 状态管理 (Pinia)

### 11.1 Store 结构

```javascript
// stores/monitor.js
{
  state: {
    totalPersons: 0,
    noHelmet: 0,
    noVest: 0,
    fall: false,
    cameraStatus: 'connected',  // 'connected' | 'disconnected'
    fps: 0,
    lastUpdate: null,           // ISO 8601 timestamp
    systemStatus: 'running',    // 'running' | 'alarming'
  }
}
```

### 11.2 派生状态 (Getters)

| Getter | 计算逻辑 |
|--------|---------|
| `hasViolation` | `noHelmet > 0 \|\| noVest > 0` |
| `hasAnyAlert` | `hasViolation \|\| fall` |
| `systemStatus` | `hasAnyAlert ? 'alarming' : 'running'` |
