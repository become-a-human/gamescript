# --header
@load "entity"
@load "joystick"

HERO = {
    "name": "Артур",
    "hp": 100,
}

class Hero(Entity):
    """Главный герой игры"""
    
    def on_create(self):
        self.hp = HERO.hp
        self.is_alive = true
    
    def heal(self, amount: int):
        self.hp = self.hp + amount
