@load "hero" like "Player"
@load "weapons"
@load "enemies"
@load "inventory"
@load "equipment"
~grab <Hero> like <MainHero>
&link <on_create> like <init>

GAME_CONFIG = {
    "title": "Hero's Quest",
    "version": "0.2.0",
    "author": "become-a-human",
}

class Game(System):
    """Главный класс игры"""

    def on_start(self):
        self.player = HERO.name
        self.weapon = SWORD.name
        self.gold = 0

    def on_update(self):
        self.gold = self.gold + 1
