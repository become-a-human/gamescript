#pragma once

#include <string>

// ========================================
// ГЛОБАЛЬНЫЕ ДАННЫЕ (сгенерировано GameScript)
// ========================================

struct GOLD_COIN_t {
    std::string name;
    int value;
    std::string sprite;
};

const GOLD_COIN_t GOLD_COIN = {
    .name = "Золотая монета",
    .value = 10,
    .sprite = "images/coin.png",
};

struct HEALTH_POTION_t {
    std::string name;
    int heal;
    std::string sprite;
};

const HEALTH_POTION_t HEALTH_POTION = {
    .name = "Зелье здоровья",
    .heal = 25,
    .sprite = "images/potion.png",
};

// ========================================
// КЛАССЫ (сгенерировано GameScript)
// ========================================

class Item : public Entity {
public:
    // Предмет на карте
    int x;
    int y;
    bool collected;

    void on_create() {
        this->x = 0;
        this->y = 0;
        this->collected = false;
    }

    void spawn(int x, int y, std::string item_type) {
        this->x = x;
        this->y = y;
        this->collected = false;
    }

};
