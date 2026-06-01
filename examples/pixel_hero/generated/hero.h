#pragma once

#include "entity.h"

#include <string>

// ========================================
// ГЛОБАЛЬНЫЕ ДАННЫЕ (сгенерировано GameScript)
// ========================================

struct HERO_t {
    std::string name;
    int hp;
    int max_hp;
    int speed;
};

const HERO_t HERO = {
    .name = "Герой",
    .hp = 100,
    .max_hp = 100,
    .speed = 4,
};

// ========================================
// КЛАССЫ (сгенерировано GameScript)
// ========================================

class Hero : public Entity {
public:
    // Главный герой
    std::string name;
    int hp;
    int max_hp;
    int speed;
    int x;
    int y;
    bool is_alive;

    void on_create() {
        this->name = HERO.name;
        this->hp = HERO.hp;
        this->max_hp = HERO.max_hp;
        this->speed = HERO.speed;
        this->x = 400;
        this->y = 300;
        this->is_alive = true;
    }

    void move(int dx, int dy) {
        this->x = this->x + dx * this->speed;
        this->y = this->y + dy * this->speed;
    }

    void take_damage(int amount) {
        this->hp = this->hp - amount;
        if (this->hp <= 0) {
            this->is_alive = false;
            this->hp = 0;
        }
    }

    void heal(int amount) {
        this->hp = this->hp + amount;
        if (this->hp > this->max_hp) {
            this->hp = this->max_hp;
        }
    }

};
