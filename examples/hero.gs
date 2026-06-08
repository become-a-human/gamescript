# --header
@load "entity"
@load "enemy"

HERO = {
    "name": "Артур",
    "hp": 100,
    "max_hp": 100,
    "mp": 50,
    "attack": 15,
    "defense": 8,
    "speed": 2.0,
    "level": 1,
    "exp": 0,
    "gold": 0,
    "is_alive": true,
}

class Hero(Entity):
    """Главный герой"""
    
    def on_create(self):
        self.name = HERO.name
        self.hp = HERO.hp
        self.max_hp = HERO.max_hp
        self.attack = HERO.attack
        self.defense = HERO.defense
        self.speed = HERO.speed
        self.level = HERO.level
        self.exp = HERO.exp
        self.gold = HERO.gold
        self.is_alive = true
    
    def take_damage(self, amount: int):
        actual = amount - self.defense
        if actual < 1:
            actual = 1
        self.hp = self.hp - actual
        print(str(actual) + " damage!")
        if self.hp <= 0:
            self.is_alive = false
            print(self.name + " died!")
    
    def heal(self, amount: int):
        self.hp = self.hp + amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        print("Healed " + str(amount))
    
    def attack_enemy(self, enemy: Enemy):
        damage = self.attack - enemy.defense
        if damage < 1:
            damage = 1
        enemy:take_damage(damage)
        print(self.name + " hits for " + str(damage))
    
    def gain_exp(self, amount: int):
        self.exp = self.exp + amount
        if self.exp >= 100:
            self.level = self.level + 1
            self.exp = 0
            self.attack = self.attack + 2
            self.max_hp = self.max_hp + 10
            self.hp = self.max_hp
            print("LEVEL UP! " + str(self.level))
