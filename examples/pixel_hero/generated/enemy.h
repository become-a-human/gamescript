#pragma once

#include "entity.h"

#include <string>

// ========================================
// ГЛОБАЛЬНЫЕ ДАННЫЕ (сгенерировано GameScript)
// ========================================

struct GOBLIN_t {
    std::string name;
    int hp;
    int attack;
    float speed;
    std::string sprite;
};

const GOBLIN_t GOBLIN = {
    .name = "Гоблин",
    .hp = 30,
    .attack = 8,
    .speed = 1.5f,
    .sprite = "images/goblin.png",
};

// ========================================
// КЛАССЫ (сгенерировано GameScript)
// ========================================

class Enemy : public Entity {
public:
    // Враг
    std::string name;
    int hp;
    int attack;
    int speed;
    int sprite;
    int x;
    int y;
    bool is_alive;
    int patrol_dir;

    void on_create() {
        this->name = GOBLIN.name;
        this->hp = GOBLIN.hp;
        this->attack = GOBLIN.attack;
        this->speed = GOBLIN.speed;
        this->sprite = GOBLIN.sprite;
        this->x = 100;
        this->y = 300;
        this->is_alive = true;
        this->patrol_dir = 1;
    }

    void patrol() {
        this->x = this->x + this->speed * this->patrol_dir;
        if (this->x > 700) {
            this->patrol_dir = -1;
        }
        if (this->x < 100) {
            this->patrol_dir = 1;
        }
    }

};
