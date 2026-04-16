import sys
sys.stdout.reconfigure(encoding="utf-8")
"""
Mock 展现层测试 — 页面 2：存读档流程
覆盖：搜索房间 → 拾取物品 → 未 look 拾取（边界）→ 使用药水 → 存档 → 读档验证 → 读不存在存档（边界）
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
print("  页面 2：存读档流程 Mock 闭环测试")
print("=" * 55)

# ── 1. 未 look 直接拾取（边界测试）──────────────────────
print("\n[1] 未 look 直接拾取（边界测试）")
status, body = req("POST", f"/session/{SESSION}/inventory/take",
                   {"item_name": "铁剑"}, prefer_code=403)
check("未 look 拾取返回 403", status == 403)
check("error 为 not_looked", body.get("error") == "not_looked")

# ── 2. 搜索房间 ──────────────────────────────────────────
print("\n[2] 搜索房间（look）")
status, body = req("POST", f"/session/{SESSION}/look")
check("POST /look 返回 200", status == 200)
check("返回 items 列表", "items" in body)
check("返回搜索消息", "message" in body)

# ── 3. 拾取存在的物品 ────────────────────────────────────
print("\n[3] 拾取铁剑")
status, body = req("POST", f"/session/{SESSION}/inventory/take", {"item_name": "铁剑"})
check("POST /take 返回 200", status == 200)
check("返回 item 信息", "item" in body)
check("返回更新后的 player_attack", "player_attack" in body)
check("返回拾取消息", "message" in body)

# ── 4. 拾取不存在的物品（边界测试）──────────────────────
print("\n[4] 拾取不存在的物品（边界测试）")
status, body = req("POST", f"/session/{SESSION}/inventory/take",
                   {"item_name": "神秘宝剑"}, prefer_code=404)
check("拾取不存在物品返回 404", status == 404)
check("error 为 item_not_found", body.get("error") == "item_not_found")

# ── 5. 查看背包 ──────────────────────────────────────────
print("\n[5] 查看背包")
status, body = req("GET", f"/session/{SESSION}/inventory")
check("GET /inventory 返回 200", status == 200)
check("返回 items 列表", "items" in body)
check("返回背包消息", "message" in body)

# ── 6. 使用药水 ──────────────────────────────────────────
print("\n[6] 使用生命药水")
status, body = req("POST", f"/session/{SESSION}/inventory/use", {"item_name": "生命药水"})
check("POST /use 返回 200", status == 200)
check("返回 player_hp", "player_hp" in body)
check("返回 healed 字段", "healed" in body)

# ── 7. 使用不存在的物品（边界测试）──────────────────────
print("\n[7] 使用不存在的物品（边界测试）")
status, body = req("POST", f"/session/{SESSION}/inventory/use",
                   {"item_name": "神秘药水"}, prefer_code=404)
check("使用不存在物品返回 404", status == 404)
check("error 为 item_not_found", body.get("error") == "item_not_found")

# ── 8. 保存游戏 ──────────────────────────────────────────
print("\n[8] 保存游戏")
status, body = req("POST", f"/session/{SESSION}/save", {"filename": "savegame.json"})
check("POST /save 返回 200", status == 200)
check("返回 filename", "filename" in body)
check("返回 saved_at 时间戳", "saved_at" in body)
check("返回保存消息", "message" in body)

# ── 9. 加载游戏 ──────────────────────────────────────────
print("\n[9] 加载游戏")
status, body = req("POST", f"/session/{SESSION}/load", {"filename": "savegame.json"})
check("POST /load 返回 200", status == 200)
check("返回 player 信息", "player" in body)
check("返回 room 信息", "room" in body)
check("返回 checkpoint_room_id", "checkpoint_room_id" in body)
check("返回 checkpoint_time", "checkpoint_time" in body)

# ── 10. 加载不存在的存档（边界测试）─────────────────────
print("\n[10] 加载不存在的存档（边界测试）")
status, body = req("POST", f"/session/{SESSION}/load",
                   {"filename": "notexist.json"}, prefer_code=404)
check("加载不存在存档返回 404", status == 404)
check("error 为 save_not_found", body.get("error") == "save_not_found")

# ── 结果汇总 ─────────────────────────────────────────────
print("\n" + "=" * 55)
print(f"  结果：{len(PASS)} 通过 / {len(FAIL)} 失败")
if FAIL:
    print(f"  失败项：{', '.join(FAIL)}")
print("=" * 55)
exit(1 if FAIL else 0)
