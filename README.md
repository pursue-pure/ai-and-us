# MUD 文字冒险游戏

一个极简主义的控制台 MUD (Multi-User Dungeon) 文字游戏引擎。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行游戏
python -m game.main
```

## 游戏命令

| 命令 | 说明 |
|------|------|
| `go <方向>` 或 `n/s/e/w` | 移动 |
| `look` 或 `l` | 查看当前房间 |
| `take <物品>` 或 `get` | 拾取物品 |
| `inventory` 或 `inv` | 查看背包 |
| `save [文件名]` | 保存游戏 |
| `load [文件名]` | 加载游戏 |
| `help` | 帮助 |
| `quit` | 退出 |

## 运行测试

```bash
pip install pytest
pytest
```

## 项目结构

```
ai-and-us/
├── game/
│   ├── __init__.py
│   ├── main.py       # 游戏入口
│   ├── engine.py     # 核心引擎
│   ├── models.py     # 数据模型
│   └── commands.py   # 命令处理
├── tests/
│   └── test_engine.py
├── requirements.txt
├── README.md
├── AI 分析备忘录.md
└── 用户故事池.md
```

## User Stories (MVP)

| ID | 功能 | 状态 |
|------|------|------|
| US-001 | 房间导航 | ✅ 已实现 |
| US-002 | 物品拾取 | ✅ 已实现 |
| US-003 | 查看状态 | ✅ 已实现 |
| US-004 | 简单战斗 | ⏳ 待实现 |
| US-005 | 游戏存档 | ✅ 已实现 |

## 开发原则

本项目的 MVP 遵循以下原则：

- ✅ 纯控制台交互，无 GUI
- ✅ 无网络功能
- ✅ 简单命令解析（关键词匹配）
