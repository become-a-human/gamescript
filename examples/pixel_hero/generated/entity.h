#pragma once

#include <string>

// ========================================
// КЛАССЫ (сгенерировано GameScript)
// ========================================

class Entity {
public:
    std::string name;
    int x;
    int y;
    int hp;
    int max_hp;
    float speed;
    std::string sprite;
    bool is_alive;

    Entity() : name(""), x(0), y(0), hp(0), max_hp(0), speed(0.0f), sprite(""), is_alive(false) {}

    void on_create() {
        this->name = "";
        this->x = 0;
        this->y = 0;
        this->hp = 100;
        this->max_hp = 100;
        this->speed = 1.0;
        this->sprite = "";
        this->is_alive = true;
    }

};
