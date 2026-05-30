# --header
@load "joystick"
@load "entity"
# ===== ГЕРОЙ =====
HERO = {
    "name": "Артур",
    "title": "Странник",
    "image": "hero.png",
    "x": 100,
    "y": 200,
    "age": 25,
    "hp": 100,
    "mp": 50,
    "max_mp": 50,
    "attack": 15,
    "defense": 8,
    "speed": 1.5,
    "level": 1,
    "exp": 0,
    "is_alive": true,
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

    def play_idle(self):
        self:set_animation("idle", 4, 10)
    
    def play_walk(self):
        self:set_animation("walk", 6, 8)

    def move_with_joystick(self, joystick: Joystick):
        if joystick.active:
            self.x = self.x + joystick.direction_x * self.speed
            self.y = self.y + joystick.direction_y * self.speed
