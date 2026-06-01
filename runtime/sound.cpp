#include <SDL2/SDL_mixer.h>

extern "C" {
    void play_sound(const char* file) {
        Mix_OpenAudio(44100, MIX_DEFAULT_FORMAT, 2, 2048);
        Mix_Chunk* chunk = Mix_LoadWAV(file);
        if (!chunk) {
            // Пробуем как музыку (MP3/OGG/MIDI)
            Mix_Music* music = Mix_LoadMUS(file);
            if (music) {
                Mix_PlayMusic(music, 1);
            }
            return;
        }
        Mix_PlayChannel(-1, chunk, 0);
    }
    
    void play_music(const char* file) {
        Mix_OpenAudio(44100, MIX_DEFAULT_FORMAT, 2, 2048);
        Mix_Music* music = Mix_LoadMUS(file);
        if (music) {
            Mix_PlayMusic(music, -1);
        }
    }
    
    void stop_music() {
        Mix_HaltMusic();
    }
}