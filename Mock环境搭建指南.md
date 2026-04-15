# Mock 环境搭建指南（Prism）

> 适用项目：`ai-and-us` MUD 洞穴探险游戏  
> 工具：[Stoplight Prism](https://github.com/stoplightio/prism) — 基于 OpenAPI 契约自动生成 Mock 服务器  
> 前提：已有 `openapi.yaml`，Node.js ≥ 18

---

## 一、安装 Prism

```bash
# 全局安装（推荐）
npm install -g @stoplight/prism-cli

# 验证安装
prism --version
```

---

## 二、启动 Mock 服务器

```bash
# 在项目根目录执行
prism mock openapi.yaml

# 默认监听 http://localhost:4010
# 输出示例：
# [CLI] ...  Prism is listening on http://127.0.0.1:4010
```

动态模式（随机返回契约中的示例数据）：

```bash
prism mock openapi.yaml --dynamic
```

---

## 三、核心业务页面闭环测试

### 业务页面 1：战斗流程

对应接口：`POST /session` → `POST /session/{id}/move` → `POST /session/{id}/attack`

```bash
# 1. 创建游戏会话
curl -X POST http://localhost:4010/session \
  -H "Content-Type: application/json" \
  -d '{"player_name": "冒险者"}'

# 预期返回 201，包含 session_id、player 初始属性、entrance 房间描述

# 2. 向北移动到阴暗走廊
curl -X POST http://localhost:4010/session/sess-001/move \
  -H "Content-Type: application/json" \
  -d '{"direction": "north"}'

# 3. 继续向东移动到哥布林营地（有敌人）
curl -X POST http://localhost:4010/session/sess-001/move \
  -H "Content-Type: application/json" \
  -d '{"direction": "east"}'

# 4. 攻击哥布林
curl -X POST http://localhost:4010/session/sess-001/attack

# 预期返回 AttackResponse，包含 player_damage、enemy_hp、counter_attack 字段
```

**边界测试：**

```bash
# 无效方向 → 预期 400
curl -X POST http://localhost:4010/session/sess-001/move \
  -H "Content-Type: application/json" \
  -d '{"direction": "up"}'

# 无敌人房间攻击 → 预期 400
curl -X POST http://localhost:4010/session/sess-001/attack

# 玩家死亡后移动 → 预期 409
curl -X POST http://localhost:4010/session/sess-001/move \
  -H "Content-Type: application/json" \
  -d '{"direction": "north"}'
```

---

### 业务页面 2：存读档流程

对应接口：`POST /session/{id}/look` → `POST /session/{id}/inventory/take` → `POST /session/{id}/save` → `POST /session/{id}/load`

```bash
# 1. 搜索房间（必须先 look 才能拾取）
curl -X POST http://localhost:4010/session/sess-001/look

# 预期返回房间物品列表

# 2. 拾取铁剑
curl -X POST http://localhost:4010/session/sess-001/inventory/take \
  -H "Content-Type: application/json" \
  -d '{"item_name": "铁剑"}'

# 预期返回 TakeResponse，包含 player_attack 更新后的值

# 3. 保存游戏
curl -X POST http://localhost:4010/session/sess-001/save \
  -H "Content-Type: application/json" \
  -d '{"filename": "savegame.json"}'

# 4. 加载游戏
curl -X POST http://localhost:4010/session/sess-001/load \
  -H "Content-Type: application/json" \
  -d '{"filename": "savegame.json"}'

# 预期返回 LoadResponse，铁剑在背包中，房间物品列表中铁剑已消失
```

**边界测试：**

```bash
# 未 look 直接拾取 → 预期 403
curl -X POST http://localhost:4010/session/sess-001/inventory/take \
  -H "Content-Type: application/json" \
  -d '{"item_name": "铁剑"}'

# 加载不存在的存档 → 预期 404
curl -X POST http://localhost:4010/session/sess-001/load \
  -H "Content-Type: application/json" \
  -d '{"filename": "notexist.json"}'
```

---

## 四、在 CI 中集成契约验证（可选）

在 `.github/workflows/ci.yml` 的 lint job 中追加：

```yaml
      - name: Validate OpenAPI contract
        run: |
          npm install -g @stoplight/prism-cli
          prism validate openapi.yaml || true
```

---

## 五、Prism 常用参数速查

| 参数 | 说明 |
|------|------|
| `--port 8080` | 指定端口（默认 4010） |
| `--dynamic` | 随机生成符合 schema 的响应数据 |
| `--errors` | 严格模式，请求不符合契约时返回错误 |
| `--cors` | 允许跨域（前端页面调试时使用） |

```bash
# 前端调试推荐启动方式
prism mock openapi.yaml --port 8080 --cors --dynamic
```

---

**最后更新：** 2026 年 4 月 15 日
