# ===== ВРАГИ =====
GOBLIN = {
    "name": str("Гоблин"),
    "hp": int(30),
    "attack": int(10),
    "defense": int(3),
    "speed": float(0.8),
    "exp_reward": int(10),
    "gold_reward": int(5),
    "loot_table": list(
        str("hp_potion"),
        str("dagger"),
    ),
    "is_boss": bool(false),
}

ORC = {
    "name": str("Орк"),
    "hp": int(80),
    "attack": int(20),
    "defense": int(8),
    "speed": float(0.5),
    "exp_reward": int(30),
    "gold_reward": int(15),
    "loot_table": list(
        str("hp_potion"),
        str("iron_helmet"),
        str("gold"),
    ),
    "is_boss": bool(false),
}

DARK_MAGE = {
    "name": str("Тёмный маг"),
    "hp": int(50),
    "attack": int(12),
    "magic_attack": int(25),
    "defense": int(4),
    "speed": float(0.6),
    "exp_reward": int(50),
    "gold_reward": int(25),
    "loot_table": list(
        str("mana_potion"),
        str("magic_staff"),
        str("ring_of_wisdom"),
    ),
    "is_boss": bool(false),
}

DRAGON_BOSS = {
    "name": str("Дракон"),
    "hp": int(500),
    "attack": int(50),
    "magic_attack": int(40),
    "defense": int(20),
    "speed": float(0.3),
    "exp_reward": int(500),
    "gold_reward": int(200),
    "loot_table": list(
        str("dragon_sword"),
        str("dragon_armor"),
        str("lucky_charm"),
        str("gold"),
        str("gold"),
    ),
    "is_boss": bool(true),
}

class Goblin(Entity):
    """Обычный гоблин"""
    
    def on_turn(self, target):
        damage = self.attack - target.defense
        if damage < 1:
            damage = 1
        target.hp -= damage

class Dragon(Entity):
    """Босс-дракон"""
    
    def on_turn(self, target):
        # Дракон атакует дважды
        damage = self.attack - target.defense
        if damage < 1:
            damage = 1
        target.hp -= damage
        target.hp -= damage