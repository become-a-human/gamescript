# ===== ГЕРОЙ =====
HERO = {
    "name": str("Артур"),
    "title": str("Странник"),
    "age": int(25),
    "hp": int(100),
    "max_hp": int(100),
    "mp": int(50),
    "max_mp": int(50),
    "attack": int(15),
    "defense": int(8),
    "speed": float(1.5),
    "level": int(1),
    "exp": int(0),
    "is_alive": bool(true),
}

class Hero(Entity):
    "Главный герой игры"
    
    def on_create(self):
        self.hp = HERO.max_hp
        self.mp = HERO.max_mp
        self.is_alive = true
    
    def take_damage(self, amount: int):
        actual = amount - self.defense
        if actual == 1:
            actual = 1
        self.hp = self.hp - actual
        if self.hp == 0:
            self.is_alive = false
    
    def heal(self, amount: int):
        self.hp = self.hp + amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
    
    def set_name(self, name: str, age: int):
        self.name = name
    
    def rest(self):
        while self.hp < self.max_hp:
            self.hp = self.hp + 1
    
    def use_all(self, items):
        for i in items:
            self:use(i)