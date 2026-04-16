import sys
sys.stdout.reconfigure(encoding="utf-8")
"""
Mock 展现层测试 — 页面 1：战斗流程
覆盖：创建会话 → 移动 → 攻击（普通命中）→ 契约结构验证 → 无效方向移动（边界）→ 死亡复活
运行前提：prism mock openapi.yaml --port 4010
"""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:4010"
SESSION = "sess-001"
PASS = []
FAIL = []


def req(method, path, body=None, prefer_code=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if prefer_code:
        headers["Prefer"] = f"code={prefer_code}"
    r = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
        print(f"  [PASS] {name}")
    else:
        FAIL.append(name)
        print(f"  [FAIL] {name}  {detail}")


print("=" * 55)
print("  页面 1：战斗流程 Mock 闭环测试")
print("=" * 55)

# ── 1. 创建会话 ──────────────────────────────────────────
print("\n[1] 创建游戏会话")
status, body = req("POST", "/session", {"player_name": "冒险者"})
check("POST /session 返回 201", status == 201)
check("返回 session_id", "session_id" in body)
check("玩家初始 HP=50", body.get("player", {}).get("hp") == 50)
check("玩家初始等级=1", body.get("player", {}).get("level") == 1)
check("起始房间为 entrance", body.get("room", {}).get("id") == "entrance")

# ── 2. 正常移动 ──────────────────────────────────────────
print("\n[2] 向北移动（正常方向）")
status, body = req("POST", f"/session/{SESSION}/move", {"direction": "north"})
check("POST /move north 返回 200", status == 200)
check("返回新房间信息", "room" in body)
check("返回移动消息", "message" in body)

# ── 3. 无效方向（边界测试）───────────────────────────────
print("\n[3] 向上移动（无效方向，边界测试）")
status, body = req("POST", f"/session/{SESSION}/move",
                   {"direction": "up"}, prefer_code=400)
check("无效方向返回 400", status == 400)
check("返回 error 字段", "error" in body)
check("error 为 invalid_direction", body.get("error") == "invalid_direction")

# ── 4. 攻击敌人（普通命中）──────────────────────────────
print("\n[4] 攻击敌人（普通命中）")
status, body = req("POST", f"/session/{SESSION}/attack")
check("POST /attack 返回 200", status == 200)
check("返回 player_damage", "player_damage" in body)
check("返回 enemy_hp", "enemy_hp" in body)
check("返回 enemy_alive", "enemy_alive" in body)
check("返回 message", "message" in body)

# ── 5. 攻击响应契约结构验证 ──────────────────────────────
print("\n[5] 攻击响应契约结构验证")
check("响应含 enemy_alive 字段", "enemy_alive" in body)
check("响应含 player_dead 字段", "player_dead" in body)

# ── 6. 玩家死亡后复活 ────────────────────────────────────
print("\n[6] 玩家死亡后复活")
status, body = req("POST", f"/session/{SESSION}/respawn")
check("POST /respawn 返回 200", status == 200)
check("返回 player_hp", "player_hp" in body)
check("返回 checkpoint_room", "checkpoint_room" in body)
check("返回 checkpoint_time", "checkpoint_time" in body)
check("HP 为 max_hp 的一半", body.get("player_hp", 0) == body.get("player_max_hp", 100) // 2)

# ── 7. 查看玩家状态 ──────────────────────────────────────
print("\n[7] 查看玩家状态")
status, body = req("GET", f"/session/{SESSION}/stats")
check("GET /stats 返回 200", status == 200)
check("返回 hp 字段", "hp" in body)
check("返回 level 字段", "level" in body)
check("返回 total_attack 字段", "total_attack" in body)

# ── 结果汇总 ─────────────────────────────────────────────
print("\n" + "=" * 55)
print(f"  结果：{len(PASS)} 通过 / {len(FAIL)} 失败")
if FAIL:
    print(f"  失败项：{', '.join(FAIL)}")
print("=" * 55)
exit(1 if FAIL else 0)
