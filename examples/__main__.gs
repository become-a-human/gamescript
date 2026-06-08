@load "entity"
@load "system"
@load "hero"
@load "enemy"
@load? "sdl_mixer"
@load? "sound"

class Main(System):
    """RPG игра со звуком"""
    
    def on_start(self):
        self.hero = Hero()
        self.hero:on_create()
        
        self.goblin = Enemy()
        self.goblin:on_create("goblin")
        
        self.orc = Enemy()
        self.orc:on_create("orc")
        
        self.turn = 0
        self.game_over = false
        
        play_music("sounds/battle.ogg")
        print("=== RPG GAME ===")
        print("Hero: " + self.hero.name)
        print("HP: " + str(self.hero.hp))
    
    def on_update(self):
        if self.game_over:
            return
        
        self.turn = self.turn + 1
        
        if self.turn == 3:
            play_sound("sounds/sword.wav")
            self.hero:attack_enemy(self.goblin)
        
        if self.turn == 5 and self.goblin.is_alive:
            self.goblin_damage = self.goblin.attack - self.hero.defense
            if self.goblin_damage < 1:
                self.goblin_damage = 1
            self.hero:take_damage(self.goblin_damage)
        
        if self.turn == 7 and self.hero.is_alive:
            play_sound("sounds/sword.wav")
            self.hero:attack_enemy(self.orc)
        
        if self.turn >= 10:
            self.game_over = true
            stop_music()
            if self.hero.is_alive:
                play_sound("sounds/victory.wav")
                print("QUEST COMPLETE!")
            else:
                play_sound("sounds/defeat.wav")
                print("GAME OVER!")
