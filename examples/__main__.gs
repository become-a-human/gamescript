@load "entity"
@load "system"
@load "screen"
@load "menu"
@load "hero"

class Main(System):
    def on_start(self):
        self.screen = MainMenu()
        self.running = true
    
    def on_update(self):
        self.gold = self.gold + 1
