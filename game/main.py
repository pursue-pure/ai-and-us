"""MUD 文字游戏 - 主入口"""
import sys
import os

# 添加父目录到路径，支持直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.commands import CommandHandler
from game.world import create_demo_world


def main():
    """主函数 - 游戏入口"""
    print("=" * 60)
    print("         🗡️  欢迎来到 MUD 洞穴探险游戏！  🐉")
    print("=" * 60)
    print()
    print("📜 故事背景：")
    print("   你是一名勇敢的冒险者，听说这个洞穴深处有一条远古巨龙，")
    print("   它守护着无数的财宝。你决定进入洞穴，击败巨龙，成为传奇！")
    print()
    print("💡 提示：")
    print("   - 输入 'help' 查看命令列表")
    print("   - 进入新房间后用 'look' 搜索物品")
    print("   - 打怪前确保 HP 充足，可以用药水恢复")
    print("   - 死亡后输入 'respawn' 复活")
    print("=" * 60)

    engine = create_demo_world()
    handler = CommandHandler(engine)
    engine.running = True

    print()
    print(engine.describe_room())
    print()

    while engine.running:
        try:
            # 检查游戏胜利
            if engine.game_won:
                print("\n🎮 游戏结束！你成功击败了巨龙，成为了传奇冒险者！")
                print("   输入 'quit' 退出游戏，或继续探索。")
                engine.game_won = False  # 重置，允许继续玩

            # 检查游戏失败（可选：可以添加死亡次数限制）

            user_input = input("> ").strip()
            if not user_input:
                continue

            result = handler.handle(user_input)
            print(result)

            # 检查是否退出
            if not engine.running:
                break

        except KeyboardInterrupt:
            print("\n👋 游戏已中断。再见！")
            break
        except EOFError:
            print("\n👋 游戏已结束。再见！")
            break


if __name__ == "__main__":
    main()
