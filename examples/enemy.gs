# --header
@load "entity"

GOBLIN = {
    "name": "Гоблин",
    "hp": 30,
    "attack": 8,
    "defense": 3,
    "exp_reward": 20,
    "gold_reward": 10,
}

ORC = {
    "name": "Орк",
    "hp": 80,
    "attack": 20,
    "defense": 8,
    "exp_reward": 50,
    "gold_reward": 30,
}

class Enemy(Entity):
    """Враг"""
    
    def on_create(self, enemy_type: str):
        if enemy_type == "goblin":
            self.name = GOBLIN.name
            self.hp = GOBLIN.hp
            self.max_hp = GOBLIN.hp
            self.attack = GOBLIN.attack
            self.defense = GOBLIN.defense
            self.exp_reward = GOBLIN.exp_reward
            self.gold_reward = GOBLIN.gold_reward
        elif enemy_type == "orc":
            self.name = ORC.name
            self.hp = ORC.hp
            self.max_hp = ORC.hp
            self.attack = ORC.attack
            self.defense = ORC.defense
            self.exp_reward = ORC.exp_reward
            self.gold_reward = ORC.gold_reward
        self.is_alive = true
    
    def take_damage(self, amount: int):
        actual = amount - self.defense
        if actual < 1:
            actual = 1
        self.hp = self.hp - actual
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = false
            print(self.name + " defeated!")
