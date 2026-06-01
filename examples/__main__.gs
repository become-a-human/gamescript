@load "entity"
@load "system"
@load "hero"
@load? "sdl_mixer"
@load? "sound"

class Main(System):
    def on_start(self):
        self.gold = 100
        print("Game started!")
    
    def on_update(self):
        self.gold = self.gold + 1
