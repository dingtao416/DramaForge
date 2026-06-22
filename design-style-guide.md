# 🎮 DramaForge — 像素卡通设计风格指南

> **核心风格定位**: 像素风 + 卡通动漫 + 经典马里奥 × 现代扁平化融合  
> **设计理念**: 在怀旧像素美学中注入现代交互体验，打造「可以玩的UI」

---

## 目录

1. [设计哲学](#1-设计哲学)
2. [色彩体系](#2-色彩体系)
3. [字体排版](#3-字体排版)
4. [像素网格系统](#4-像素网格系统)
5. [按钮设计](#5-按钮设计)
6. [图标系统](#6-图标系统)
7. [间距与布局](#7-间距与布局)
8. [组件样式](#8-组件样式)
9. [动效规范](#9-动效规范)
10. [插图与角色](#10-插图与角色)

---

## 1. 设计哲学

### 1.1 核心原则

| 原则 | 说明 |
|------|------|
| **像素即语言** | 所有视觉元素以像素为单位对齐，拒绝半像素渲染 |
| **8px 神圣法则** | 一切尺寸、间距、圆角以 8 为基数 |
| **高饱和度优先** | 鲜艳、明亮、对比强烈 — 致敬 8-bit 时代 |
| **卡通化反馈** | 每一个交互都有夸张的视觉回应 |
| **触感第一** | 按钮像游戏里的砖块，按下要有"弹"的感觉 |

### 1.2 风格关键词

```
像素艺术 · 8-bit · 16-bit · NES配色 · 描边线条 · 卡通表情
问号砖块 · 蘑菇王国 · 金币闪烁 · 管道绿色 · 星星无敌
```

---

## 2. 色彩体系

### 2.1 主色调 — 马里奥经典红蓝

```
┌─────────────────────────────────────────────────────────┐
│  🟥 Primary Red     #E52521    hsl(1, 79%, 51%)        │
│  🟦 Sky Blue        #5DADE2    hsl(204, 70%, 63%)      │
│  🟨 Coin Gold       #F1C40F    hsl(48, 89%, 50%)       │
│  🟩 Pipe Green      #2ECC71    hsl(145, 63%, 49%)      │
└─────────────────────────────────────────────────────────┘
```

### 2.2 完整色板

#### 功能色 (Semantic Colors)

| Token | 色值 | 用途 | 马里奥梗 |
|-------|------|------|----------|
| `--color-primary` | `#E52521` | 主按钮、强调色 | 🔴 马里奥帽子红 |
| `--color-primary-hover` | `#C41E1A` | 主按钮悬停 | 深红蘑菇 |
| `--color-primary-active` | `#A01815` | 主按钮按下 | 按扁的蘑菇 |
| `--color-secondary` | `#5DADE2` | 次要按钮、链接 | 🔵 马里奥背带裤蓝 |
| `--color-secondary-hover` | `#4A90C4` | 次要按钮悬停 | 深蓝天空 |
| `--color-accent` | `#F1C40F` | 高亮、金币元素 | 🟡 金币！ |
| `--color-accent-hover` | `#D4A90D` | 悬停金 | 暗金币 |
| `--color-success` | `#2ECC71` | 成功状态 | 🟢 1UP 蘑菇绿 |
| `--color-warning` | `#F39C12` | 警告状态 | 🟠 超级蘑菇橙 |
| `--color-error` | `#E74C3C` | 错误状态 | 🔴 库巴红 |
| `--color-info` | `#3498DB` | 信息提示 | 🔵 冰花蓝 |

#### 背景色

| Token | 色值 | 用途 |
|-------|------|------|
| `--bg-canvas` | `#1A1A2E` | 页面底层背景（深色星空） |
| `--bg-surface` | `#16213E` | 卡片/面板背景 |
| `--bg-elevated` | `#1F3460` | 悬浮层背景 |
| `--bg-overlay` | `rgba(0,0,0,0.7)` | 遮罩层 |

#### 文字色

| Token | 色值 | 用途 |
|-------|------|------|
| `--text-primary` | `#FFFFFF` | 主文字 |
| `--text-secondary` | `#B0C4DE` | 次要文字 |
| `--text-muted` | `#6C7A89` | 禁用/辅助文字 |
| `--text-on-primary` | `#FFFFFF` | 主色上的文字 |

#### 像素描边色

| Token | 色值 | 用途 |
|-------|------|------|
| `--border-pixel` | `#2C3E50` | 常规像素边框 |
| `--border-accent` | `#F1C40F` | 强调像素边框（金币框） |
| `--border-hover` | `#E52521` | 悬停边框 |

### 2.3 CSS 变量定义

```css
:root {
  /* === 主色系 === */
  --pixel-red:       #E52521;
  --pixel-red-dark:  #C41E1A;
  --pixel-red-deep:  #A01815;
  --pixel-blue:      #5DADE2;
  --pixel-blue-dark: #4A90C4;
  --pixel-gold:      #F1C40F;
  --pixel-gold-dark: #D4A90D;
  --pixel-green:     #2ECC71;
  --pixel-green-dark:#27AE60;
  --pixel-orange:    #F39C12;
  --pixel-orange-dark:#D68910;
  
  /* === 马里奥经典色 === */
  --mario-red:       #E52521;   /* 帽子/衬衫 */
  --mario-blue:      #5DADE2;   /* 背带裤 */
  --mario-skin:      #FDBF6F;   /* 肤色 */
  --mario-brown:     #8B4513;   /* 鞋子/头发 */
  --mario-yellow:    #F1C40F;   /* 纽扣/金币 */
  
  /* === UI功能色映射 === */
  --color-primary:          var(--pixel-red);
  --color-primary-hover:    var(--pixel-red-dark);
  --color-primary-active:   var(--pixel-red-deep);
  --color-secondary:        var(--pixel-blue);
  --color-secondary-hover:  var(--pixel-blue-dark);
  --color-accent:           var(--pixel-gold);
  --color-success:          var(--pixel-green);
  --color-warning:          var(--pixel-orange);
  --color-error:            #E74C3C;
  --color-info:             #3498DB;
  
  /* === 背景系统 === */
  --bg-canvas:    #1A1A2E;
  --bg-surface:   #16213E;
  --bg-elevated:  #1F3460;
  --bg-overlay:   rgba(0, 0, 0, 0.75);
  
  /* === 文字系统 === */
  --text-primary:    #FFFFFF;
  --text-secondary:  #B0C4DE;
  --text-muted:      #6C7A89;
  --text-on-primary: #FFFFFF;
  
  /* === 边框系统 === */
  --border-pixel:  #2C3E50;
  --border-accent: var(--pixel-gold);
  --border-hover:  var(--pixel-red);
}
```

---

## 3. 字体排版

### 3.1 字体族

```css
/* 像素风格标题 — 等宽像素字体 */
--font-pixel: 'Press Start 2P', 'Zpix', 'Minecraft', monospace;

/* 正文/UI — 圆体卡通字体 */
--font-display: 'Fredoka One', 'Bubblegum Sans', cursive;

/* 代码/数据 — 像素等宽 */
--font-mono: 'Fira Code', 'Press Start 2P', monospace;

/* 系统降级 */
--font-system: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### 3.2 字体大小阶梯（基于 8px）

| Name | Size | Line Height | 用途 |
|------|------|-------------|------|
| `text-xs` | 10px | 16px | 辅助标注、像素小字 |
| `text-sm` | 12px | 16px | 说明文字、标签 |
| `text-base` | 16px | 24px | 正文 |
| `text-lg` | 20px | 28px | 小标题 |
| `text-xl` | 24px | 32px | 卡片标题 |
| `text-2xl` | 32px | 40px | 页面标题 |
| `text-3xl` | 40px | 48px | 大标题（带像素描边） |
| `text-4xl` | 56px | 64px | Hero 标题（像素艺术字） |

### 3.3 像素文字特效

```css
/* 像素描边标题 — 马里奥标题同款 */
.pixel-title {
  font-family: var(--font-pixel);
  font-size: 2rem;
  color: #fff;
  text-shadow:
    -2px -2px 0 #000,   /* 左上黑色描边 */
     2px -2px 0 #000,   /* 右上 */
    -2px  2px 0 #000,   /* 左下 */
     2px  2px 0 #000,   /* 右下 */
     0    4px 0 #E52521,/* 红色投影 */
     0    6px 8px rgba(0,0,0,0.5);
  letter-spacing: 4px;
  image-rendering: pixelated;
}

/* 彩虹渐变文字 — 无敌星效果 */
.rainbow-text {
  background: linear-gradient(90deg, 
    #E52521, #F39C12, #F1C40F, #2ECC71, #5DADE2, #9B59B6, #E52521);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: rainbow-scroll 2s linear infinite;
}
```

---

## 4. 像素网格系统

### 4.1 基准单位

```
┌─────────────────────────────────────────────┐
│                                             │
│       全 部 以  8 p x  为 基 数             │
│                                             │
│   1 unit = 8px                              │
│   所有尺寸必须是 8 的整数倍                    │
│                                             │
│   ✅ 8, 16, 24, 32, 40, 48, 56, 64...      │
│   ❌ 5, 10, 15, 25, 30, 35, 45...           │
│                                             │
└─────────────────────────────────────────────┘
```

### 4.2 像素渲染模式

```css
/* 全局像素渲染 */
* {
  image-rendering: crisp-edges;       /* 保持像素锐利 */
  image-rendering: pixelated;         /* 缩放时保持像素块 */
}

/* 像素边框专用类 */
.pixel-border {
  border: 2px solid var(--border-pixel);
  box-shadow: 
    inset -3px -3px 0 0 rgba(0,0,0,0.3),  /* 内阴影 — 右下深色 */
    inset 3px 3px 0 0 rgba(255,255,255,0.15); /* 内阴影 — 左上亮色 */
}

/* 凸起/凹陷效果 — 经典按钮触感 */
.pixel-raised {
  border: 2px solid;
  border-color: #fff #555 #555 #fff;  /* 左上亮 右下暗 */
}

.pixel-pressed {
  border: 2px solid;
  border-color: #555 #fff #fff #555;  /* 左上暗 右下亮 → 按下的视觉 */
}
```

---

## 5. 按钮设计

### 5.1 按钮尺寸体系

```
┌──────────────────────────────────────────────────────────────┐
│                       按钮尺寸表                              │
├──────────┬──────────┬─────────┬───────────┬──────────────────┤
│   尺寸    │  高度    │ 水平内边距│  字体     │    使用场景       │
├──────────┼──────────┼─────────┼───────────┼──────────────────┤
│   xs     │  24px    │  12px   │  text-xs  │ 标签/徽章/微型    │
│   sm     │  32px    │  16px   │  text-sm  │ 表格操作/辅助     │
│   md     │  40px    │  24px   │  text-base│ 常规按钮(默认)    │
│   lg     │  48px    │  32px   │  text-lg  │ 主要操作/CTA      │
│   xl     │  56px    │  40px   │  text-xl  │ Hero按钮/大CTA    │
│   砖块   │  48px    │  24px   │  text-lg  │ 特殊像素砖块按钮   │
└──────────┴──────────┴─────────┴───────────┴──────────────────┘
```

### 5.2 按钮样式变体

#### 🔴 主按钮 — 马里奥红砖块

```css
.btn-primary {
  height: 48px;
  padding: 0 32px;
  font-family: var(--font-pixel);
  font-size: 14px;
  color: #FFFFFF;
  background: var(--pixel-red);
  border: 3px solid #A01815;
  border-radius: 2px;          /* 几乎直角，像素感 */
  box-shadow:
    inset -4px -4px 0 0 rgba(0, 0, 0, 0.25),
    inset 4px 4px 0 0 rgba(255, 255, 255, 0.2),
    4px 4px 0 0 #A01815;       /* 立体投影 */
  cursor: pointer;
  transition: all 0.1s ease;
  letter-spacing: 2px;
  image-rendering: pixelated;
}

.btn-primary:hover {
  background: var(--pixel-red-dark);
  box-shadow:
    inset -4px -4px 0 0 rgba(0, 0, 0, 0.25),
    inset 4px 4px 0 0 rgba(255, 255, 255, 0.2),
    2px 2px 0 0 #A01815;       /* 悬停时投影缩小 */
  transform: translate(2px, 2px); /* 向投影方向移动 — 像真的被按了 */
}

.btn-primary:active {
  background: var(--pixel-red-deep);
  box-shadow:
    inset 4px 4px 0 0 rgba(0, 0, 0, 0.3),  /* 内阴影翻转 */
    inset -4px -4px 0 0 rgba(255, 255, 255, 0.1);
  transform: translate(4px, 4px);            /* 完全按下 */
}
```

#### 🟡 问号砖块按钮 — 特殊交互按钮

```css
.btn-mystery {
  height: 48px;
  padding: 0 32px;
  font-family: var(--font-pixel);
  font-size: 14px;
  color: #F1C40F;
  background: repeating-linear-gradient(
    45deg,
    #E67E22 0px,
    #E67E22 4px,
    #F39C12 4px,
    #F39C12 8px
  );
  border: 3px solid #A04000;
  border-radius: 2px;
  box-shadow:
    inset -4px -4px 0 rgba(0,0,0,0.3),
    4px 4px 0 #A04000;
  animation: question-blink 1.5s ease-in-out infinite;
}

@keyframes question-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.9; }
}

.btn-mystery:active {
  animation: none;
  box-shadow: inset 4px 4px 0 rgba(0,0,0,0.3);
  transform: translate(4px, 4px);
}
```

#### 🔵 次要按钮 — 天空蓝

```css
.btn-secondary {
  height: 40px;
  padding: 0 24px;
  font-family: var(--font-pixel);
  font-size: 12px;
  color: #FFFFFF;
  background: var(--pixel-blue);
  border: 3px solid #3A7CA5;
  border-radius: 2px;
  box-shadow:
    inset -3px -3px 0 0 rgba(0,0,0,0.2),
    3px 3px 0 0 #3A7CA5;
  cursor: pointer;
  transition: all 0.1s ease;
  letter-spacing: 1px;
}

.btn-secondary:hover {
  background: var(--pixel-blue-dark);
  box-shadow:
    inset -3px -3px 0 rgba(0,0,0,0.2),
    1px 1px 0 #3A7CA5;
  transform: translate(2px, 2px);
}

.btn-secondary:active {
  box-shadow: inset 3px 3px 0 rgba(0,0,0,0.3);
  transform: translate(3px, 3px);
}
```

#### 🟩 幽灵按钮 — 透明描边

```css
.btn-ghost {
  height: 40px;
  padding: 0 24px;
  font-family: var(--font-pixel);
  font-size: 12px;
  color: var(--pixel-green);
  background: transparent;
  border: 2px solid var(--pixel-green);
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.1s ease;
  letter-spacing: 1px;
}

.btn-ghost:hover {
  background: rgba(46, 204, 113, 0.15);
  box-shadow: 0 0 12px rgba(46, 204, 113, 0.3); /* 荧光效果 */
}
```

#### ⭐ 无敌星按钮 — 渐变闪耀

```css
.btn-star {
  height: 48px;
  padding: 0 32px;
  font-family: var(--font-pixel);
  font-size: 14px;
  color: #FFFFFF;
  background: linear-gradient(135deg, #F1C40F, #F39C12, #E67E22);
  background-size: 200% 200%;
  border: 3px solid #D4A90D;
  border-radius: 2px;
  box-shadow:
    inset -4px -4px 0 0 rgba(0, 0, 0, 0.25),
    4px 4px 0 0 #B8860B,
    0 0 20px rgba(241, 196, 15, 0.4);    /* 外发光 */
  animation: star-shine 2s ease-in-out infinite;
  cursor: pointer;
}

@keyframes star-shine {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
```

### 5.3 按钮间距规范

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   按钮之间间距 = 16px (2单位)                             │
│   按钮组与内容间距 = 24px (3单位)                          │
│   按钮内文字与图标间距 = 8px (1单位)                       │
│                                                         │
│   [ 按钮A ]  ← 16px →  [ 按钮B ]                        │
│                                                         │
│   [ 按钮A ]  ← 24px →  下方内容                          │
│                                                         │
│   [ 🎮 按钮 ]  图标←→文字 = 8px                          │
│      └─8px─┘                                            │
│                                                         │
│   组合按钮（吸附在一起）间距 = 0px，中间按钮无圆角           │
│   [ 左 ] [ 中 ] [ 右 ]                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

```css
/* 按钮组水平间距 */
.btn-group {
  display: flex;
  gap: 16px;             /* 按钮间距 = 2单位 */
  align-items: center;
}

/* 按钮组垂直间距 */
.btn-group-vertical {
  display: flex;
  flex-direction: column;
  gap: 12px;             /* 垂直按钮间距稍小 = 1.5单位 */
}

/* 按钮与下方内容的间距 */
.btn + .content {
  margin-top: 24px;      /* 3单位 */
}

/* 图标 + 文字按钮 */
.btn > .icon + span {
  margin-left: 8px;      /* 1单位 */
}

/* 吸附式按钮组（如 左/中/右 分段按钮） */
.btn-segment {
  display: flex;
  gap: 0;                /* 无间距 */
}
.btn-segment > .btn:first-child { border-radius: 2px 0 0 2px; }
.btn-segment > .btn:last-child  { border-radius: 0 2px 2px 0; }
.btn-segment > .btn:not(:first-child):not(:last-child) {
  border-radius: 0;
  border-left: none;
  border-right: none;
}
```

### 5.4 按钮状态一览

```
                    default        hover          active        disabled
                    ────────       ───────       ────────       ────────
┌─────────┐
│ Primary │     🔴 亮红         🔴 深红         🔴 暗红         ⚫ 灰色
│          │     凸起状态        半按下(x+2)     全按下(x+4)     无投影
├─────────┤
│Secondary│     🔵 亮蓝         🔵 深蓝         🔵 暗蓝         ⚫ 灰色
├─────────┤
│ Mystery │     🟡 闪烁纹理     停止闪烁        按下状态          ⚫ 灰色
├─────────┤
│  Ghost  │     🟩 透明描边     🟩 荧光背景     🟩 填充背景      ⚫ 灰色描边
├─────────┤
│  Star   │     ⭐ 渐变流动     ⭐ 加速动画      ⭐ 按下          ⚫ 灰色
└─────────┘
```

---

## 6. 图标系统

### 6.1 图标设计原则

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   ① 所有图标采用 24×24px 画布（3单位）                  │
│   ② 线条粗细 = 2px（不可缩放），渲染为像素块               │
│   ③ 使用像素级对齐（snap to pixel grid）               │
│   ④ 描边风格 + 卡通化表达                              │
│   ⑤ 彩色图标色板与UI色彩体系一致                         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 6.2 图标尺寸阶梯

| Size | 像素 | 网格单位 | 用途 |
|------|------|----------|------|
| xs | 16×16 | 2u | 内联图标、徽章图标 |
| sm | 24×24 | 3u | 按钮内图标（默认） |
| md | 32×32 | 4u | 导航图标、列表图标 |
| lg | 48×48 | 6u | 功能图标、状态图标 |
| xl | 64×64 | 8u | 空状态插图、占位图标 |
| 2xl | 96×96 | 12u | 英雄区装饰图标 |

### 6.3 核心图标库（像素马里奥主题）

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  🍄 蘑菇图标      — 用户/账户               (24×24)       │
│  ⭐ 星星图标      — 收藏/精选/AI 功能        (24×24)       │
│  🪙 金币图标      — 积分/点数/充值            (24×24)       │
│  ❓ 问号砖块      — 帮助/提示/未知            (24×24)       │
│  🌷 火花图标      — 创意/AI 生成/灵感         (24×24)       │
│  🏠 城堡图标      — 首页/主页                (32×32)       │
│  🗺️ 地图图标      — 导航/目录                (32×32)       │
│  🎬 场记板        — 项目/剧集                (32×32)       │
│  📜 卷轴图标      — 剧本/文档                (32×32)       │
│  🎨 调色板        — 素材/资源库              (32×32)       │
│  ⚙️ 齿轮图标      — 设置                     (24×24)       │
│  💾 存档点        — 保存                     (24×24)       │
│  ⬆️ 绿色管道      — 上传/导出                (24×24)       │
│  🚩 终点旗        — 完成/发布                (32×32)       │
│  👻 幽灵图标      — 删除/移除                (24×24)       │
│  ❤️ 心形图标      — 喜欢/生命值              (16×16)       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 6.4 图标CSS实现

```css
/* 基础图标 */
.icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--icon-size, 24px);
  height: var(--icon-size, 24px);
  image-rendering: pixelated;
  flex-shrink: 0;
}

/* 像素图标描边效果 */
.icon-pixel {
  filter: drop-shadow(2px 2px 0 rgba(0,0,0,0.3));
}

/* 金币旋转动画图标 */
.icon-coin {
  animation: coin-spin 0.8s steps(4) infinite;
}
@keyframes coin-spin {
  0% { transform: rotateY(0deg); }
  100% { transform: rotateY(360deg); }
}

/* 问号图标弹跳 */
.icon-mystery {
  animation: mystery-bounce 1s ease-in-out infinite;
}
@keyframes mystery-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
```

### 6.5 按钮内图标位置规范

```
   ┌─────────────────────────────┐
   │  [🎬]  开始创作              │  ← 图标在左，图标-文字间距 8px
   └─────────────────────────────┘
   
   ┌─────────────────────────────┐
   │  下一页  [▶]                │  ← 图标在右
   └─────────────────────────────┘
   
   ┌──────────────────┐
   │       [⚙️]        │  ← 纯图标按钮（图标居中）
   └──────────────────┘
```

```css
/* 图标左置按钮 */
.btn-icon-left {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

/* 图标右置按钮 */
.btn-icon-right {
  display: inline-flex;
  align-items: center;
  flex-direction: row-reverse;
  gap: 8px;
}

/* 纯图标按钮（正方形） */
.btn-icon-only {
  width: 40px;      /* 与高度一致 */
  height: 40px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
```

---

## 7. 间距与布局

### 7.1 间距标尺（基于 8px）

```
    0px     不适用（合并元素）
    4px     极小间距 — 图标与标签之间
    8px     1单位 — 相关元素紧密组合
   12px     1.5单位 — 段落内间距
   16px     2单位 — 按钮间距、表单元素间距 ★推荐默认★
   20px     2.5单位 — 卡片内元素间距
   24px     3单位 — 卡片内边距、区块间距
   32px     4单位 — 区域分隔
   40px     5单位 — 大区块分隔
   48px     6单位 — 章节间距
   64px     8单位 — 页面级间距
   80px    10单位 — 首页大型区块间距
```

### 7.2 页面布局

```
┌─────────────────────────────────────────────────────┐
│                   页面最大宽度                         │
│                    1200px                              │
│                                                       │
│   ┌───────────────────────────────────────────────┐  │
│   │              顶部导航栏  64px                    │  │
│   │  [🍄 Logo]  [导航1] [导航2] ...  [👤 用户]     │  │
│   ├───────────────────────────────────────────────┤  │
│   │                                               │  │
│   │  ← 48px padding →  [内容区]  ← 48px →         │  │
│   │                                               │  │
│   │    各区块间距 64px                              │  │
│   │                                               │  │
│   │    卡片栅格间距 24px (列) × 24px (行)           │  │
│   │                                               │  │
│   │    [卡片]  [卡片]  [卡片]                       │  │
│   │    [卡片]  [卡片]  [卡片]                       │  │
│   │                                               │  │
│   ├───────────────────────────────────────────────┤  │
│   │              底部  56px                          │  │
│   └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

```css
/* 布局变量 */
:root {
  --page-max-width: 1200px;
  --page-padding-x: 48px;        /* 页面水平内边距 = 6单位 */
  --page-padding-y: 64px;        /* 页面垂直内边距 = 8单位 */
  --section-gap: 64px;           /* 章节间距 = 8单位 */
  --card-gap: 24px;              /* 卡片间距 = 3单位 */
  --content-gap: 16px;           /* 内容元素间距 = 2单位 */
  --navbar-height: 64px;         /* 顶部导航高度 = 8单位 */
  --footer-height: 56px;         /* 底部高度 */
}
```

### 7.3 卡片内边距

```
┌──────────────────────────────┐
│  ← 24px padding            │
│  ┌────────────────────────┐ │
│  │ Card Header            │ │
│  │ [Icon] Title           │ │
│  ├────────────────────────┤ │  ← 16px 间距
│  │                        │ │
│  │ Content Area           │ │
│  │                        │ │
│  ├────────────────────────┤ │  ← 16px 间距
│  │ [Cancel]    [Confirm]  │ │  ← 按钮间距 16px
│  └────────────────────────┘ │
│  ← 24px padding            │
└──────────────────────────────┘
```

```css
.card {
  background: var(--bg-surface);
  border: 2px solid var(--border-pixel);
  border-radius: 2px;
  padding: 24px;                         /* 内边距 = 3单位 */
  box-shadow:
    inset -2px -2px 0 rgba(0,0,0,0.2),
    4px 4px 0 rgba(0,0,0,0.3);           /* 像素立体投影 */
}

.card-header {
  margin-bottom: 16px;                   /* 标题与内容间距 */
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-pixel);
  font-size: 14px;
  color: var(--pixel-gold);
}

.card-body {
  /* 内容区域 */
}

.card-footer {
  margin-top: 16px;                      /* 内容与操作间距 */
  display: flex;
  justify-content: flex-end;
  gap: 16px;                             /* 按钮间距 = 2单位 */
}
```

---

## 8. 组件样式

### 8.1 输入框

```css
.input {
  height: 40px;
  padding: 0 16px;
  font-family: var(--font-pixel);
  font-size: 12px;
  color: #FFFFFF;
  background: rgba(0, 0, 0, 0.3);
  border: 2px solid var(--border-pixel);
  border-radius: 2px;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  letter-spacing: 1px;
}

.input:focus {
  border-color: var(--pixel-gold);
  box-shadow: 0 0 0 3px rgba(241, 196, 15, 0.25); /* 金色聚焦环 */
}

.input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: rgba(0, 0, 0, 0.2);
}

.input::placeholder {
  color: var(--text-muted);
  font-size: 10px;
}

/* 带像素图标的输入框 */
.input-with-icon {
  position: relative;
}
.input-with-icon .icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
}
.input-with-icon input {
  padding-left: 44px;  /* 12px(icon左) + 24px(icon) + 8px(gap) */
}
```

### 8.2 下拉选择器

```css
.select {
  height: 40px;
  padding: 0 36px 0 16px;
  font-family: var(--font-pixel);
  font-size: 12px;
  color: #FFFFFF;
  background: rgba(0, 0, 0, 0.3);
  background-image: url("data:image/svg+xml,..."); /* 像素三角箭头 */
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 12px 8px;
  border: 2px solid var(--border-pixel);
  border-radius: 2px;
  appearance: none;
  cursor: pointer;
}

.select:focus {
  border-color: var(--pixel-gold);
  box-shadow: 0 0 0 3px rgba(241, 196, 15, 0.25);
}
```

### 8.3 开关组件 — 像素拨动开关

```css
/* 拨动开关 — 灵感来自马里奥开关方块 */
.toggle {
  width: 48px;
  height: 24px;
  background: #555;
  border: 2px solid #333;
  border-radius: 2px;
  cursor: pointer;
  position: relative;
  transition: background 0.15s ease;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.4);
}

.toggle::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 16px;
  background: #E74C3C;      /* 红色开关块 — 未激活 */
  border: 2px solid #C0392B;
  border-radius: 1px;
  box-shadow: inset -2px -2px 0 rgba(0,0,0,0.2);
  transition: left 0.15s ease, background 0.15s ease;
}

.toggle.active {
  background: #2ECC71;       /* 绿色背景 — 激活状态 */
}

.toggle.active::after {
  left: 24px;                /* 滑到右边 */
  background: #27AE60;       /* 绿色开关块 */
  border-color: #1E8449;
}
```

### 8.4 标签/徽章

```css
/* 像素标签 */
.badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  font-family: var(--font-pixel);
  font-size: 8px;
  color: #FFFFFF;
  background: var(--pixel-red);
  border: 2px solid #A01815;
  border-radius: 2px;
  letter-spacing: 1px;
  box-shadow: inset -2px -2px 0 rgba(0,0,0,0.2);
}

.badge-gold {
  background: var(--pixel-gold);
  border-color: #B8860B;
  color: #5D3A00;
}

.badge-green {
  background: var(--pixel-green);
  border-color: #1E8449;
}

/* 蘑菇标签 — 半圆形 */
.badge-mushroom {
  border-radius: 12px 12px 2px 2px;  /* 上圆下方 = 蘑菇形状 */
}
```

### 8.5 对话框/模态窗

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-surface);
  border: 3px solid var(--border-accent);        /* 金色边框 */
  border-radius: 2px;
  padding: 32px;
  min-width: 400px;
  max-width: 560px;
  box-shadow:
    0 0 0 4px rgba(0, 0, 0, 0.3),               /* 外层黑色像素投影 */
    8px 8px 0 rgba(0, 0, 0, 0.4);
  image-rendering: pixelated;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  font-family: var(--font-pixel);
  font-size: 16px;
  color: var(--pixel-gold);
}

.modal-body {
  margin-bottom: 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
}
```

### 8.6 进度条 — 马力条

```css
/* 像素进度条 — 马里奥生命条风格 */
.progress-bar {
  height: 16px;
  background: #2C3E50;
  border: 2px solid #1A252F;
  border-radius: 2px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.4);
}

.progress-bar-fill {
  height: 100%;
  background: repeating-linear-gradient(
    90deg,
    var(--pixel-green) 0px,
    var(--pixel-green) 4px,
    #27AE60 4px,
    #27AE60 8px
  );
  border-right: 2px solid #1E8449;
  transition: width 0.3s steps(8);  /* 阶梯式动画 — 像素感 */
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.3);
}

/* 金币进度条 */
.progress-bar-coin .progress-bar-fill {
  background: repeating-linear-gradient(
    90deg,
    var(--pixel-gold) 0px,
    var(--pixel-gold) 4px,
    #D4A90D 4px,
    #D4A90D 8px
  );
}
```

### 8.7 工具提示

```css
/* 像素风格 Tooltip */
.tooltip {
  position: relative;
}

.tooltip::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  padding: 6px 12px;
  font-family: var(--font-pixel);
  font-size: 8px;
  color: #FFFFFF;
  background: #1A1A2E;
  border: 2px solid #F1C40F;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;
  z-index: 999;
  box-shadow: 3px 3px 0 rgba(0,0,0,0.4);
}

.tooltip:hover::after {
  opacity: 1;
}
```

---

## 9. 动效规范

### 9.1 动效时长

```
┌─────────────────────────────────────┐
│  微交互 (micro)      100ms          │  ← 按钮悬停/按下
│  过渡 (transition)   150-200ms      │  ← 颜色/位置过渡
│  入场 (enter)        250-350ms      │  ← 元素出现
│  退场 (exit)         150-250ms      │  ← 元素消失
│  循环 (loop)         1-3s           │  ← 装饰动画
│  页面转场            300-400ms      │  ← 路由切换
└─────────────────────────────────────┘
```

### 9.2 缓动函数

```css
/* 像素弹跳缓动 — 方块落地感 */
--ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);

/* 按钮按下缓动 — 快速响应 */
--ease-press: cubic-bezier(0.2, 0, 0, 1);

/* 入场缓动 — 自然出现 */
--ease-enter: cubic-bezier(0.4, 0, 0.2, 1);

/* 弹窗出现 — 游戏提示框感 */
--ease-popup: cubic-bezier(0.175, 0.885, 0.32, 1.275);
```

### 9.3 关键帧动画

```css
/* 金币收集动画 */
@keyframes coin-collect {
  0%   { transform: translateY(0) rotateY(0) scale(1); opacity: 1; }
  50%  { transform: translateY(-24px) rotateY(360deg) scale(1.3); opacity: 1; }
  100% { transform: translateY(-48px) rotateY(720deg) scale(0.5); opacity: 0; }
}

/* 砖块顶击动画 */
@keyframes brick-bump {
  0%   { transform: translateY(0); }
  30%  { transform: translateY(-8px); }
  60%  { transform: translateY(0); }
  80%  { transform: translateY(-3px); }
  100% { transform: translateY(0); }
}

/* 蘑菇出现动画 */
@keyframes mushroom-pop {
  0%   { transform: translateY(16px) scaleY(0.1); opacity: 0; }
  60%  { transform: translateY(-4px) scaleY(1.1); opacity: 1; }
  100% { transform: translateY(0) scaleY(1); opacity: 1; }
}

/* 像素闪烁 — 无敌状态 */
@keyframes pixel-flash {
  0%, 100% { filter: brightness(1); }
  25%  { filter: brightness(1.3); }
  50%  { filter: brightness(1.6); }
  75%  { filter: brightness(1.3); }
}

/* 上下浮动 — 闲置装饰 */
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

/* 像素溶解 — 消失效果 */
@keyframes pixel-dissolve {
  0%   { filter: none; opacity: 1; }
  100% { filter: url(#pixelate); opacity: 0; }
}

/* 页面入场 — 从下弹入 */
@keyframes slide-up-bounce {
  0%   { transform: translateY(32px); opacity: 0; }
  60%  { transform: translateY(-8px); opacity: 1; }
  100% { transform: translateY(0); opacity: 1; }
}
```

### 9.4 场景动效应用

```css
/* 页面路由切换 */
.page-enter-active {
  animation: slide-up-bounce 0.35s var(--ease-bounce);
}

.page-leave-active {
  animation: pixel-dissolve 0.2s ease;
}

/* 列表项交错入场 */
.list-item-enter {
  opacity: 0;
  transform: translateX(-16px);
}
.list-item-enter-active {
  transition: all 0.25s var(--ease-bounce);
}
/* 通过 animation-delay 实现交错效果 */
.list-item:nth-child(1) { animation-delay: 0ms; }
.list-item:nth-child(2) { animation-delay: 50ms; }
.list-item:nth-child(3) { animation-delay: 100ms; }
.list-item:nth-child(4) { animation-delay: 150ms; }
.list-item:nth-child(5) { animation-delay: 200ms; }

/* 悬停微动效 */
.card-hoverable {
  transition: transform 0.15s var(--ease-bounce), box-shadow 0.15s ease;
}
.card-hoverable:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 0 rgba(0,0,0,0.3);
}
```

---

## 10. 插图与角色

### 10.1 空状态插图

```
┌────────────────────────────────────────────┐
│                                            │
│         [像素风格空状态插图]                 │
│                                            │
│         ┌──────────────────┐               │
│         │   ?  ?  ?  ?    │               │
│         │  ┌──────────┐   │               │
│         │  │  EMPTY!  │   │   ← 像素砖块   │
│         │  │          │   │     文字提示    │
│         │  └──────────┘   │               │
│         │   ?  ?  ?  ?    │               │
│         └──────────────────┘               │
│                                            │
│    还没有内容，点击按钮开始创作吧！            │
│                                            │
│       [🍄 立即开始]                         │
│                                            │
└────────────────────────────────────────────┘
```

### 10.2 加载状态

```css
/* 马里奥奔跑加载动画 */
.loading-mario {
  width: 32px;
  height: 32px;
  background: url('mario-run-spritesheet.png');
  background-size: auto 100%;
  animation: mario-run 0.6s steps(3) infinite;
}
@keyframes mario-run {
  0% { background-position: 0 0; }
  100% { background-position: -96px 0; }
}

/* 金币旋转加载 */
.loading-coin {
  width: 24px;
  height: 24px;
  animation: coin-spin 0.8s steps(4) infinite;
}

/* 问号砖块加载（三个点弹跳） */
.loading-dots {
  display: flex;
  gap: 8px;
}
.loading-dots span {
  width: 8px;
  height: 8px;
  background: var(--pixel-gold);
  animation: dot-bounce 0.6s ease infinite alternate;
}
.loading-dots span:nth-child(2) { animation-delay: 0.15s; }
.loading-dots span:nth-child(3) { animation-delay: 0.3s; }
@keyframes dot-bounce {
  0% { transform: translateY(0); }
  100% { transform: translateY(-12px); }
}
```

### 10.3 装饰元素

```css
/* 像素草地 */
.pixel-grass {
  height: 8px;
  background: repeating-linear-gradient(
    90deg,
    #2ECC71 4px, #27AE60 4px, #27AE60 8px
  );
}

/* 像素云朵 */
.pixel-cloud {
  width: 48px;
  height: 16px;
  background: #FFFFFF;
  border-radius: 0;
  position: relative;
}
.pixel-cloud::before {
  content: '';
  position: absolute;
  top: -8px;
  left: 8px;
  width: 24px;
  height: 16px;
  background: #FFFFFF;
}
.pixel-cloud::after {
  content: '';
  position: absolute;
  top: -4px;
  right: 8px;
  width: 16px;
  height: 12px;
  background: #FFFFFF;
}

/* 像素星星装饰 */
.pixel-star {
  width: 16px;
  height: 16px;
  background: var(--pixel-gold);
  clip-path: polygon(
    50% 0%, 61% 35%, 98% 35%, 68% 57%,
    79% 91%, 50% 70%, 21% 91%, 32% 57%,
    2% 35%, 39% 35%
  );
  animation: float 3s ease-in-out infinite;
}

/* 像素问号 */
.pixel-question {
  font-family: var(--font-pixel);
  font-size: 20px;
  color: #F1C40F;
  animation: mystery-bounce 1.5s ease-in-out infinite;
}
```

---

## 附录

### A. 设计资源推荐

| 资源 | 用途 | 链接 |
|------|------|------|
| Press Start 2P | 像素英文字体 | Google Fonts |
| Zpix / 最像素 | 像素中文/日文字体 | GitHub |
| Aseprite | 像素画绘制工具 | aseprite.org |
| Piskel | 在线像素画编辑器 | piskelapp.com |
| NES.css | NES风格CSS框架（参考） | GitHub |
| 8-bit Sfx | 像素风格音效库 | freesound.org |

### B. CSS 框架集成建议

本项目（Vue 3 + Vite）推荐方式：

```scss
// styles/pixel-theme.scss
// 将所有像素风格变量导入为 SCSS/CSS 变量
// 配合 UnoCSS / Tailwind CSS 使用自定义主题

// 示例：Tailwind 主题扩展
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        pixel: ['"Press Start 2P"', 'monospace'],
        cartoon: ['"Fredoka One"', 'cursive'],
      },
      colors: {
        pixel: {
          red: '#E52521',
          blue: '#5DADE2',
          gold: '#F1C40F',
          green: '#2ECC71',
        }
      },
      spacing: {
        // 基于 8px 网格的间距别名
        '1u': '8px',
        '2u': '16px',
        '3u': '24px',
        '4u': '32px',
        '6u': '48px',
        '8u': '64px',
      },
      borderRadius: {
        pixel: '2px',   // 全局像素圆角
      },
      boxShadow: {
        'pixel-sm': '2px 2px 0 rgba(0,0,0,0.3)',
        'pixel-md': '4px 4px 0 rgba(0,0,0,0.3)',
        'pixel-lg': '6px 6px 0 rgba(0,0,0,0.3)',
      }
    }
  }
}
```

### C. 检查清单

设计稿评审时请逐项确认：

- [ ] 是否所有尺寸都是 8 的整数倍？
- [ ] 按钮是否有"凸起→按下"的立体像素效果？
- [ ] 主色是否为马里奥红 `#E52521`？
- [ ] 交互元素是否有 hover/active 状态（尤其是"按下"的位移效果）？
- [ ] 字体是否正确使用像素字体 / 卡通圆体？
- [ ] 圆角是否统一为 2px（直角像素感）？
- [ ] 图标是否为像素风格，线条粗 2px？
- [ ] 间距是否遵循 8px 网格基准？
- [ ] 动效是否使用 steps() 或 cubic-bezier 弹跳缓动？
- [ ] 色彩饱和度是否足够高（符合卡通动漫风格）？

---

> 🍄 **It's-a me, Mario!** — 记住，好的像素风格设计不只是"马赛克"，而是在限制中创造乐趣。
> 每一个像素都有它的位置，每一个块都有它的重量，每一次按下都要有"嘭"的反馈！
