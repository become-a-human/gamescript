# --header
@load "entity"
# ===== ВРАГИ =====
GOBLIN = {
    "name": "Гоблин",
    "hp": 30,
    "attack": 10,
    "defense": 3,
    "speed": 0.8,
    "exp_reward": 10,
    "gold_reward": 5,
    "loot_table": list(
        "hp_potion",
        "dagger",
    ),
    "is_boss": false,
}

ORC = {
    "name": "Орк",
    "hp": 80,
    "attack": 20,
    "defense": 8,
    "speed": 0.5,
    "exp_reward": 30,
    "gold_reward": 15,
    "loot_table": list(
        "hp_potion",
        "iron_helmet",
        "gold",
    ),
    "is_boss": false,
}

DARK_MAGE = {
    "name": "Тёмный маг",
    "hp": 50,
    "attack": 12,
    "magic_attack": 25,
    "defense": 4,
    "speed": 0.6,
    "exp_reward": 50,
    "gold_reward": 25,
    "loot_table": list(
        "mana_potion",
        "magic_staff",
        "ring_of_wisdom",
    ),
    "is_boss": false,
}

DRAGON_BOSS = {
    "name": "Дракон",
    "hp": 500,
    "attack": 50,
    "magic_attack": 40,
    "defense": 20,
    "speed": 0.3,
    "exp_reward": 500,
    "gold_reward": 200,
    "loot_table": list(
        "dragon_sword",
        "dragon_armor",
        "lucky_charm",
        "gold",
        "gold",
    ),
    "is_boss": true,
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