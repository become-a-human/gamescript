#pragma once

#include "joystick.h"
#include "entity.h"

#include <string>

// ========================================
// ГЛОБАЛЬНЫЕ ДАННЫЕ (сгенерировано GameScript)
// ========================================

struct HERO_t {
    std::string name;
    std::string title;
    std::string image;
    int x;
    int y;
    int age;
    int hp;
    int mp;
    int max_mp;
    int attack;
    int defense;
    float speed;
    int level;
    int exp;
    bool is_alive;
};

const HERO_t HERO = {
    .name = "Артур",
    .title = "Странник",
    .image = "hero.png",
    .x = 100,
    .y = 200,
    .age = 25,
    .hp = 100,
    .mp = 50,
    .max_mp = 50,
    .attack = 15,
    .defense = 8,
    .speed = 1.5f,
    .level = 1,
    .exp = 0,
    .is_alive = true,
};

// ========================================
// КЛАССЫ (сгенерировано GameScript)
// ========================================

class Hero : public Entity {
public:
    // Главный герой игры
    int hp;
    int mp;
    bool is_alive;
    std::string name;

    void on_create();
    void take_damage(int amount);
    void heal(int amount);
    void set_name(std::string name, int age);
    void rest();
    void use_all(int items);
};
