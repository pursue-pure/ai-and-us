const canvas = document.querySelector("#mapCanvas");
const ctx = canvas.getContext("2d");
const logEl = document.querySelector("#log");
const roomNameEl = document.querySelector("#roomName");
const roomDescriptionEl = document.querySelector("#roomDescription");
const playerNameEl = document.querySelector("#playerName");
const playerMetaEl = document.querySelector("#playerMeta");
const hpBarEl = document.querySelector("#hpBar");
const hpTextEl = document.querySelector("#hpText");
const enemyBoxEl = document.querySelector("#enemyBox");
const itemListEl = document.querySelector("#itemList");
const inventoryListEl = document.querySelector("#inventoryList");

let sessionId = "";
let state = null;

const positions = {
  entrance: { x: 110, y: 260 },
  hall: { x: 250, y: 260 },
  goblin_camp: { x: 390, y: 260 },
  treasure: { x: 530, y: 260 },
  orc_hall: { x: 530, y: 140 },
  armory: { x: 530, y: 40 },
  boss_lair: { x: 760, y: 40 },
};

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return response.json();
}

function writeLog(message) {
  if (!message) return;
  logEl.textContent = message;
}

async function createSession() {
  state = await request("/session", {
    method: "POST",
    body: JSON.stringify({ player_name: "冒险者" }),
  });
  sessionId = state.session_id;
  render();
  writeLog(state.message);
}

async function action(path, body) {
  if (!sessionId) return;
  try {
    state = await request(`/session/${sessionId}${path}`, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
    render();
    writeLog(state.message);
  } catch (error) {
    writeLog(`请求失败：${error.message}`);
  }
}

function makeChip(item, onClick) {
  const button = document.createElement("button");
  button.className = `chip ${item.type || ""}`;
  button.type = "button";
  button.textContent = item.effect ? `${item.name} +${item.effect}` : item.name;
  button.title = item.description || item.name;
  button.addEventListener("click", onClick);
  return button;
}

function renderList(container, items, emptyText, handler) {
  container.innerHTML = "";
  if (!items.length) {
    const empty = document.createElement("span");
    empty.className = "chip";
    empty.textContent = emptyText;
    container.appendChild(empty);
    return;
  }
  items.forEach((item) => container.appendChild(makeChip(item, () => handler(item))));
}

function renderStats() {
  const player = state.player;
  const room = state.room;
  const hpPercent = Math.max(0, Math.min(100, (player.hp / player.max_hp) * 100));

  playerNameEl.textContent = player.name;
  playerMetaEl.textContent = `LV.${player.level} · 攻击 ${player.attack} · 经验 ${player.xp}`;
  hpBarEl.style.width = `${hpPercent}%`;
  hpTextEl.textContent = `${player.hp}/${player.max_hp}`;
  roomNameEl.textContent = room.name;
  roomDescriptionEl.textContent = room.description;

  if (room.enemy && room.enemy.alive) {
    enemyBoxEl.classList.remove("hidden");
    enemyBoxEl.textContent = `${room.enemy.name} HP ${room.enemy.hp}/${room.enemy.max_hp} · 攻击 ${room.enemy.attack}`;
  } else {
    enemyBoxEl.classList.add("hidden");
    enemyBoxEl.textContent = "";
  }

  renderList(itemListEl, room.items || [], "未发现", (item) => {
    action("/inventory/take", { item_name: item.name });
  });
  renderList(inventoryListEl, player.inventory || [], "空", (item) => {
    action("/inventory/use", { item_name: item.name });
  });
}

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.max(640, Math.floor(rect.width * ratio));
  canvas.height = Math.max(360, Math.floor(rect.height * ratio));
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
}

function drawMap() {
  resizeCanvas();
  const rect = canvas.getBoundingClientRect();
  const scaleX = rect.width / 880;
  const scaleY = rect.height / 420;
  const toScreen = (pos) => ({ x: pos.x * scaleX + 30, y: pos.y * scaleY + 30 });

  ctx.clearRect(0, 0, rect.width, rect.height);
  ctx.fillStyle = "#15191a";
  ctx.fillRect(0, 0, rect.width, rect.height);

  if (!state) return;

  ctx.lineWidth = 4;
  ctx.strokeStyle = "#465256";
  state.world.forEach((room) => {
    const from = positions[room.id];
    if (!from) return;
    Object.values(room.exits).forEach((targetId) => {
      const to = positions[targetId];
      if (!to) return;
      const a = toScreen(from);
      const b = toScreen(to);
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    });
  });

  state.world.forEach((room) => {
    const pos = positions[room.id];
    if (!pos) return;
    const p = toScreen(pos);
    const active = room.id === state.player.current_room;

    ctx.beginPath();
    ctx.arc(p.x, p.y, active ? 28 : 22, 0, Math.PI * 2);
    ctx.fillStyle = active ? "#e8b95e" : room.is_boss_room ? "#7e4040" : "#263033";
    ctx.fill();
    ctx.strokeStyle = room.has_enemy ? "#e45d5d" : "#64c7d8";
    ctx.lineWidth = active ? 4 : 2;
    ctx.stroke();

    ctx.fillStyle = active ? "#101314" : "#f3efe7";
    ctx.font = "13px Microsoft YaHei, Segoe UI, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(room.name.replace(/^[^\u4e00-\u9fa5A-Za-z]+/, ""), p.x, p.y + 46);
  });
}

function render() {
  renderStats();
  drawMap();
}

document.querySelectorAll("[data-move]").forEach((button) => {
  button.addEventListener("click", () => action("/move", { direction: button.dataset.move }));
});

document.querySelector("#lookBtn").addEventListener("click", () => action("/look"));
document.querySelector("#attackBtn").addEventListener("click", () => action("/attack"));
document.querySelector("#respawnBtn").addEventListener("click", () => action("/respawn"));
document.querySelector("#saveBtn").addEventListener("click", () => action("/save", { filename: "savegame-web.json" }));
document.querySelector("#loadBtn").addEventListener("click", () => action("/load", { filename: "savegame-web.json" }));
document.querySelector("#newGameBtn").addEventListener("click", createSession);

document.querySelector("#commandForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.querySelector("#commandInput");
  if (!input.value.trim()) return;
  await action("/command", { command: input.value.trim() });
  input.value = "";
});

window.addEventListener("resize", drawMap);

createSession().catch((error) => writeLog(`启动失败：${error.message}`));
