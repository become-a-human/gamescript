@load "sdl2"
@load "sdl2_image"
@load "entity"
@load "system"
@load "hero"

class Main(System):
    """Точка входа — генерирует int main()"""
    
    def on_start(self):
        self.gold = 100
        self.running = true
    
    def on_update(self):
        self.gold = self.gold + 1
