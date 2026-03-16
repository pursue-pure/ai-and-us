"""命令处理器"""
from .engine import GameEngine


class CommandHandler:
    """命令处理器 - 解析并执行玩家输入"""
    
    def __init__(self, engine: GameEngine):
        self.engine = engine
        self.commands = {
            "go": self.cmd_go,
            "north": self.cmd_north,
            "south": self.cmd_south,
            "east": self.cmd_east,
            "west": self.cmd_west,
            "n": self.cmd_north,
            "s": self.cmd_south,
            "e": self.cmd_east,
            "w": self.cmd_west,
            "look": self.cmd_look,
            "l": self.cmd_look,
            "take": self.cmd_take,
            "get": self.cmd_take,
            "inventory": self.cmd_inventory,
            "inv": self.cmd_inventory,
            "i": self.cmd_inventory,
            "save": self.cmd_save,
            "load": self.cmd_load,
            "help": self.cmd_help,
            "quit": self.cmd_quit,
        }
    
    def handle(self, user_input: str) -> str:
        """处理用户输入"""
        parts = user_input.strip().lower().split()
        if not parts:
            return "请输入命令。"
        
        command = parts[0]
        args = parts[1:]
        
        if command in self.commands:
            return self.commands[command](args)
        else:
            return f"未知命令：{command}。输入 'help' 查看帮助。"
    
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
        return self.engine.describe_room()
    
    def cmd_take(self, args: list) -> str:
        if not args:
            return "拿什么？用法：take <物品名>"
        item_name = " ".join(args)
        return self.engine.take_item(item_name)
    
    def cmd_inventory(self, args: list) -> str:
        return self.engine.show_inventory()
    
    def cmd_save(self, args: list) -> str:
        filename = args[0] if args else "savegame.json"
        return self.engine.save_game(filename)
    
    def cmd_load(self, args: list) -> str:
        filename = args[0] if args else "savegame.json"
        return self.engine.load_game(filename)
    
    def cmd_help(self, args: list) -> str:
        return """
=== 帮助 ===
移动：go <方向> 或 n/s/e/w (方向：north/south/east/west)
查看：look (或 l) - 查看当前房间
物品：take <物品> (或 get) - 拾取物品
背包：inventory (或 inv, i) - 查看背包
存档：save [文件名] - 保存游戏
读档：load [文件名] - 加载游戏
其他：help - 帮助，quit - 退出
"""
    
    def cmd_quit(self, args: list) -> str:
        self.engine.running = False
        return "感谢游玩，再见！"
