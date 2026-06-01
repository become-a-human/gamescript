@load "entity"
@load "system"
@load "hero"
@load "joystick"
@load "calculator"
@load "rng"
@load "clock"
@load "aabb"
@load? "sdl_mixer"
@load? "sound"

class Main(System):
    """Точка входа — генерирует int main()"""
    
    def on_start(self):
        self.gold = 100
        self.running = true
        self.hero = Hero()
        self.hero:on_create()
        print("Game started!")
    
    def on_update(self):
        self.gold = self.gold + 1
        self.hero:update_animation()
        if self.gold >= 1000:
            self.gold = 0
