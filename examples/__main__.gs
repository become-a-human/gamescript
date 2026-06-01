@load "entity"
@load "system"
@load "hero"

class Main(System):
    def on_start(self):
        self.gold = 100
        print("Game started!")
        play_sound("start.wav")
    
    def on_update(self):
        self.gold = self.gold + 1
