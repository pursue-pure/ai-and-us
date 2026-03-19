"""命令处理器"""
import re

from .engine import GameEngine


class CommandHandler:
    """命令处理器 - 解析并执行玩家输入"""
    
    def __init__(self, engine: GameEngine):
        self.engine = engine
        self.commands = {
            # 移动命令
            "go": self.cmd_go,
            "north": self.cmd_north,
            "south": self.cmd_south,
            "east": self.cmd_east,
            "west": self.cmd_west,
            "n": self.cmd_north,
            "s": self.cmd_south,
            "e": self.cmd_east,
            "w": self.cmd_west,
            # 查看命令
            "look": self.cmd_look,
            "l": self.cmd_look,
            "search": self.cmd_look,
            # 物品命令
            "take": self.cmd_take,
            "get": self.cmd_take,
            "pick": self.cmd_take,
            "inventory": self.cmd_inventory,
            "inv": self.cmd_inventory,
            "i": self.cmd_inventory,
            "use": self.cmd_use,
            # 战斗命令
            "attack": self.cmd_attack,
            "kill": self.cmd_attack,
            "fight": self.cmd_attack,
            # 状态命令
            "stats": self.cmd_stats,
            "status": self.cmd_stats,
            "hp": self.cmd_stats,
            # 系统命令
            "save": self.cmd_save,
            "load": self.cmd_load,
            "respawn": self.cmd_respawn,
            "help": self.cmd_help,
            "quit": self.cmd_quit,
            "exit": self.cmd_quit,
        }
    
    def handle(self, user_input: str) -> str:
        """处理用户输入"""
        command, args = self._parse_input(user_input)
        if not command:
            return "💭 请输入命令。输入 'help' 查看帮助。"

        if command in self.commands:
            return self.commands[command](args)
        else:
            return f"❓ 未知命令：{command}。输入 'help' 查看帮助。"

    def _parse_input(self, user_input: str) -> tuple[str, list[str]]:
        """解析命令并容错常见输入格式。"""
        text = user_input.strip().lower()
        if not text:
            return "", []

        # 支持 take<铁剑> / take <铁剑> / use<生命药水>
        angle_match = re.match(r"^([a-z]+)\s*<\s*(.*?)\s*>$", text)
        if angle_match:
            cmd = angle_match.group(1)
            arg = angle_match.group(2).strip()
            return cmd, [arg] if arg else []

        parts = text.split()
        if not parts:
            return "", []

        cmd = parts[0]
        args = parts[1:]

        # 支持 take铁剑 / use生命药水 这类命令与参数黏连输入
        for verb in ("take", "get", "pick", "use", "go"):
            if cmd.startswith(verb) and cmd != verb:
                suffix = cmd[len(verb):].strip()
                cmd = verb
                if suffix:
                    args = [suffix] + args
                break

        return cmd, args
    
    def cmd_go(self, args: list) -> str:
        if not args:
            return "往哪走？用法：go <方向> 或 n/s/e/w"
        direction = args[0]
        if direction == "to" and len(args) > 1:
            direction = args[1]
        return self.engine.move_player(direction)
    
    def cmd_north(self, args: list) -> str:
        return self.engine.move_player("north")
    
    def cmd_south(self, args: list) -> str:
        return self.engine.move_player("south")
    
    def cmd_east(self, args: list) -> str:
        return self.engine.move_player("east")
    
    def cmd_west(self, args: list) -> str:
        return self.engine.move_player("west")
    
    def cmd_look(self, args: list) -> str:
        return self.engine.look()
    
    def cmd_take(self, args: list) -> str:
        if not args:
            return "拿什么？用法：take <物品名>"
        item_name = " ".join(args).strip()
        item_name = item_name.strip("<>").strip()
        return self.engine.take_item(item_name)
    
    def cmd_inventory(self, args: list) -> str:
        return self.engine.show_inventory()
    
    def cmd_use(self, args: list) -> str:
        if not args:
            return "使用什么？用法：use <物品名>"
        item_name = " ".join(args).strip()
        item_name = item_name.strip("<>").strip()
        return self.engine.use_item(item_name)
    
    def cmd_attack(self, args: list) -> str:
        return self.engine.attack_enemy()
    
    def cmd_stats(self, args: list) -> str:
        return self.engine.show_stats()
    
    def cmd_save(self, args: list) -> str:
        filename = args[0] if args else "savegame.json"
        return self.engine.save_game(filename)
    
    def cmd_load(self, args: list) -> str:
        filename = args[0] if args else "savegame.json"
        return self.engine.load_game(filename)
    
    def cmd_respawn(self, args: list) -> str:
        return self.engine.respawn()
    
    def cmd_help(self, args: list) -> str:
        return """
╔═══════════════════════════════════════════════════════════╗
║                    📖 MUD 游戏命令帮助                     ║
╠═══════════════════════════════════════════════════════════╣
║  🚶 移动                                                  ║
║    go <方向> 或 n/s/e/w   向指定方向移动                   ║
║    方向：north(n), south(s), east(e), west(w)             ║
╠═══════════════════════════════════════════════════════════╣
║  👀 查看                                                  ║
║    look (l)               搜索房间，发现物品               ║
║    stats (status, hp)     查看角色状态                     ║
╠═══════════════════════════════════════════════════════════╣
║  🎒 物品                                                  ║
║    take <物品>            拾取物品                         ║
║    inventory (inv, i)     查看背包                         ║
║    use <物品>             使用物品（如药水）               ║
╠═══════════════════════════════════════════════════════════╣
║  ⚔️  战斗                                                  ║
║    attack (kill, fight)   攻击当前房间的敌人               ║
║    respawn                死亡后复活                       ║
╠═══════════════════════════════════════════════════════════╣
║  💾 系统                                                  ║
║    save [文件名]          保存游戏                         ║
║    load [文件名]          加载游戏                         ║
║    help                   显示此帮助                       ║
║    quit (exit)            退出游戏                         ║
╚═══════════════════════════════════════════════════════════╝
"""
    
    def cmd_quit(self, args: list) -> str:
        self.engine.running = False
        return "👋 感谢游玩，再见！"
