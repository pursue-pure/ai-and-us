"""默认游戏世界组装。"""
from .engine import GameEngine
from .models import Enemy, Item, Room


def create_demo_world(player_name: str = "冒险者") -> GameEngine:
    """创建演示世界 - 洞穴探险打怪游戏。"""
    engine = GameEngine()

    entrance = Room(
        id="entrance",
        name="🕳️ 洞穴入口",
        description="你站在一个阴暗潮湿的洞穴入口。冷风从北面吹来，带来阵阵寒意。"
        "墙壁上有一些模糊的涂鸦，似乎是前人留下的警告。",
        exits={"north": "hall"},
        items=[Item("火把", "一个普通的木制火把", "tool", 0)],
        last_room="",
    )

    hall = Room(
        id="hall",
        name="📍 阴暗走廊",
        description="这是一个狭窄的地下走廊。墙壁上闪烁着微弱的蓝色光芒，"
        "空气中弥漫着潮湿的霉味。远处传来奇怪的声响。",
        exits={"south": "entrance", "east": "goblin_camp"},
        items=[Item("生命药水", "一瓶红色的药水", "potion", 25)],
        last_room="entrance",
    )

    goblin_camp = Room(
        id="goblin_camp",
        name="💀 哥布林营地",
        description="这里是一个简陋的营地，地上散落着破烂的帐篷和骨头。"
        "空气中充满了哥布林特有的恶臭。",
        exits={"west": "hall", "east": "treasure"},
        enemy=Enemy(
            name="👺 哥布林斥候",
            description="一个瘦小的哥布林，手持生锈的匕首，眼神凶狠。",
            hp=20,
            max_hp=20,
            attack=5,
            reward_xp=30,
        ),
        items=[Item("哥布林匕首", "一把生锈的匕首", "weapon", 3)],
        last_room="hall",
    )

    treasure = Room(
        id="treasure",
        name="💎 宝藏室",
        description="金光闪闪！这里堆满了财宝。墙壁上镶嵌着宝石，中央有一个华丽的宝箱。",
        exits={"west": "goblin_camp", "north": "orc_hall"},
        items=[
            Item("大生命药水", "一瓶金色的药水", "potion", 50),
            Item("铁剑", "一把锋利的铁剑", "weapon", 8),
        ],
        last_room="goblin_camp",
    )

    orc_hall = Room(
        id="orc_hall",
        name="👹 兽人大厅",
        description="这是一个宽敞的大厅，四周摆放着兽人的战旗和武器架。"
        "地上有战斗留下的痕迹，空气中弥漫着血腥味。",
        exits={"south": "treasure", "north": "armory"},
        enemy=Enemy(
            name="🐗 兽人战士",
            description="一个强壮的兽人，身穿皮甲，手持巨大的战斧，肌肉发达。",
            hp=40,
            max_hp=40,
            attack=10,
            reward_xp=60,
        ),
        items=[Item("兽人战斧", "一把沉重的战斧", "weapon", 12)],
        last_room="treasure",
    )

    armory = Room(
        id="armory",
        name="⚔️  武器库",
        description="这里是一个古老的武器库。墙上挂满了各种武器，中央的剑台上插着一把散发着光芒的宝剑。",
        exits={"south": "orc_hall", "north": "boss_lair"},
        items=[
            Item("超级药水", "一瓶闪耀着彩虹光芒的药水", "potion", 100),
            Item("圣剑", "一把散发着神圣光芒的宝剑", "weapon", 20),
        ],
        last_room="orc_hall",
    )

    boss_lair = Room(
        id="boss_lair",
        name="🐉 BOSS 巢穴",
        description="这是一个巨大的洞穴，四周堆满了骸骨。洞穴深处，"
        "一双红色的眼睛正盯着你。强大的威压让你几乎无法呼吸。",
        exits={"south": "armory"},
        enemy=Enemy(
            name="🐲 远古巨龙",
            description="一条巨大的黑龙，鳞片如钢铁般坚硬，口中喷吐着火焰。"
            "它是这个洞穴的主宰，无数冒险者都倒在它的利爪之下。",
            hp=100,
            max_hp=100,
            attack=15,
            reward_xp=500,
        ),
        is_boss_room=True,
        last_room="armory",
    )

    for room in [entrance, hall, goblin_camp, treasure, orc_hall, armory, boss_lair]:
        engine.add_room(room)

    engine.create_player(player_name, "entrance")
    return engine
