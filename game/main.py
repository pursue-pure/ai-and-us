"""MUD 文字游戏 - 主入口"""
from .engine import GameEngine
from .commands import CommandHandler
from .models import Room, Item


def create_demo_world() -> GameEngine:
    """创建演示世界"""
    engine = GameEngine()
    
    # 创建房间
    room1 = Room(
        id="entrance",
        name="洞穴入口",
        description="你站在一个阴暗潮湿的洞穴入口。冷风从北面吹来。",
        exits={"north": "hall"},
        items=[Item("火把", "一个普通的木制火把")]
    )
    
    room2 = Room(
        id="hall",
        name="大厅",
        description="这是一个宽敞的地下大厅。墙壁上闪烁着微弱的光芒。",
        exits={"south": "entrance", "east": "treasure", "west": "monster"}
    )
    
    room3 = Room(
        id="treasure",
        name="宝藏室",
        description="金光闪闪！这里堆满了财宝。",
        exits={"west": "hall"},
        items=[Item("金币", "一袋闪闪发光的金币"), Item("宝剑", "一把锋利的铁剑")]
    )
    
    room4 = Room(
        id="monster",
        name="怪物巢穴",
        description="一股恶臭扑面而来。黑暗中有什么东西在移动...",
        exits={"east": "hall"},
        items=[Item("骨头", "一根不知名生物的骨头")]
    )
    
    # 添加房间到引擎
    for room in [room1, room2, room3, room4]:
        engine.add_room(room)
    
    # 创建玩家
    engine.create_player("冒险者", "entrance")
    
    return engine


def main():
    """主函数 - 游戏入口"""
    print("=" * 40)
    print("     欢迎来到 MUD 文字冒险游戏！")
    print("=" * 40)
    
    engine = create_demo_world()
    handler = CommandHandler(engine)
    engine.running = True
    
    print("\n输入 'help' 查看命令列表，'quit' 退出游戏。\n")
    print(engine.describe_room())
    print()
    
    while engine.running:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue
            
            result = handler.handle(user_input)
            print(result)
            
        except KeyboardInterrupt:
            print("\n游戏已中断。再见！")
            break
        except EOFError:
            print("\n游戏已结束。再见！")
            break


if __name__ == "__main__":
    main()
