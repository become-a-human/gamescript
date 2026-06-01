# --header
# ВНИМАНИЕ: требует SDL2_mixer. Не тестировалось на Termux.
@load "sdl_mixer"

class Audio(System):
    def play_sfx(self, file: str):
        play_sound(file)
    
    def play_bgm(self, file: str):
        play_music(file)
    
    def stop_bgm(self):
        stop_music()
