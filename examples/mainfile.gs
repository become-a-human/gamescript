@load "sdl2"
@load "sdl2_image"
@load "hero"
@load "weapons"
@load "enemies"
@load "inventory"
@load "equipment"
~grab <Hero> like <MainHero>
&link <on_create> like <init>

GAME_CONFIG = {
    "title": "Hero's Quest",
    "version": "0.3.0",
    "author": "become-a-human",
}

class Game(System):
    """Главный класс игры"""

    def on_start(self):
        self.gold = 100
        self.name = "Test Game"

    def on_update(self):
        self.gold = self.gold + 1
