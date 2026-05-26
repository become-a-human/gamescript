@load "hero"
@load "weapons"

GAME_CONFIG = {
    "title": str("Hero's Quest"),
    "version": str("0.1.0"),
    "author": str("become-a-human"),
}

class Game(System):
    """Главный класс игры"""
    
    def on_start(self):
        self.player = HERO.name
        self.weapon = SWORD.name
