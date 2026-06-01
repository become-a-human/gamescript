@load "entity"
@load "system"

class Hero(Entity):
    def on_create(self):
        self.name = "Герой"
        self.hp = 100

class Main(System):
    def on_start(self):
        self.hero_name = "Герой"
        self.hero_hp = 100
        self.hero_x = 400
        self.gold = 0
        print("Game started!")
    
    def on_update(self):
        self.gold = self.gold + 1
        self.hero_x = self.hero_x + 1
        if self.hero_x > 800:
            self.hero_x = 0
