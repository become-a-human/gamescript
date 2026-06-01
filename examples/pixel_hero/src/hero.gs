# --header
@load "entity"

HERO = {
    "name": "Герой",
    "hp": 100,
    "max_hp": 100,
    "speed": 4,
}

class Hero(Entity):
    """Главный герой"""
    
    def on_create(self):
        self.name = HERO.name
        self.hp = HERO.hp
        self.max_hp = HERO.max_hp
        self.speed = HERO.speed
        self.x = 400
        self.y = 300
        self.is_alive = true
    
    def move(self, dx: int, dy: int):
        self.x = self.x + dx * self.speed
        self.y = self.y + dy * self.speed
    
    def take_damage(self, amount: int):
        self.hp = self.hp - amount
        if self.hp <= 0:
            self.is_alive = false
            self.hp = 0
    
    def heal(self, amount: int):
        self.hp = self.hp + amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
