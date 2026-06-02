@load "entity"
@load "system"
@load "hero"

class Main(System):
    """Точка входа — консольная игра"""
    
    def on_start(self):
        self.hero = Hero()
        self.hero:on_create()
        self.gold = 0
        self.score = 0
        self.running = true
        print("=== GameScript Console Game ===")
        print("Hero ready")
        print("HP: " + str(self.hero.hp))
    
    def on_update(self):
        self.score = self.score + 1
        if self.score % 10 == 0:
            print("Score: " + str(self.score))
        if self.score >= 50:
            self.running = false
            print("WIN!")
