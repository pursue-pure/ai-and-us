"""战斗与状态结算服务"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..models import Player, Room


@dataclass
class LevelUpResult:
    new_level: int
    hp_bonus: int
    attack_bonus: int
    xp_gained: int


@dataclass
class CounterAttackResult:
    damage: int
    player_hp: int
    player_dead: bool


@dataclass
class CombatResult:
    player_damage: int
    enemy_hp: int
    enemy_alive: bool
    counter_attack: Optional[CounterAttackResult] = None
    level_up: Optional[LevelUpResult] = None
    boss_victory: bool = False
    player_dead: bool = False
    messages: list = field(default_factory=list)


class CombatService:
    """战斗服务 — 负责战斗流程控制与状态结算，不依赖 GameEngine。"""

    def __init__(self):
        self._last_death_time: str = ""

    @property
    def last_death_time(self) -> str:
        return self._last_death_time

    def attack(self, player: Player, room: Room) -> CombatResult:
        """战斗主入口，返回结构化 CombatResult。"""
        enemy = room.enemy
        player_damage = self._apply_player_attack(player, enemy)

        result = CombatResult(
            player_damage=player_damage,
            enemy_hp=enemy.hp,
            enemy_alive=enemy.is_alive(),
            messages=[f"⚔️  你攻击了 {enemy.name}，造成 {player_damage} 点伤害！"],
        )

        if not enemy.is_alive():
            self._resolve_victory(player, room, enemy, result)
        else:
            self._resolve_counter_attack(player, enemy, result)

        return result

    def _apply_player_attack(self, player: Player, enemy) -> int:
        """计算并应用玩家伤害，返回实际伤害值。"""
        damage = player.get_attack_power()
        enemy.take_damage(damage)
        return damage

    def _resolve_victory(self, player: Player, room: Room, enemy, result: CombatResult) -> None:
        """结算经验、升级与 BOSS 胜利。"""
        player.xp += enemy.reward_xp
        result.messages.append(f"🎉 你击败了 {enemy.name}！获得 {enemy.reward_xp} 经验值！")

        if player.xp >= player.level * 50:
            player.level_up()
            result.level_up = LevelUpResult(
                new_level=player.level,
                hp_bonus=20,
                attack_bonus=5,
                xp_gained=enemy.reward_xp,
            )
            result.messages.append(f"⭐ 升级了！当前等级：LV.{player.level}")
            result.messages.append("   最大生命值 HP +20，且生命值已回满；攻击 +5")

        if room.is_boss_room:
            result.boss_victory = True
            result.messages.append("")
            result.messages.append("=" * 40)
            result.messages.append("🏆 恭喜！你击败了最终 BOSS，游戏胜利！")
            result.messages.append("=" * 40)

        room.enemy = None

    def _resolve_counter_attack(self, player: Player, enemy, result: CombatResult) -> None:
        """处理敌人反击和玩家死亡。"""
        damage = enemy.attack
        player.take_damage(damage)

        result.counter_attack = CounterAttackResult(
            damage=damage,
            player_hp=player.hp,
            player_dead=not player.is_alive,
        )
        result.messages.append(f"💥 {enemy.name}反击，对你造成 {damage} 点伤害！")
        result.messages.append(f"   你的 HP: {player.hp}/{player.max_hp}")

        if not player.is_alive:
            self._last_death_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result.player_dead = True
            result.messages.append("")
            result.messages.append("💀 你被打败了...")
            result.messages.append("你将回档到检查点。输入 'respawn' 继续游戏。")
