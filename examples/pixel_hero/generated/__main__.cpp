#include "entity.h"
#include "system.h"

#include <iostream>
#include <string>

// ========================================
// КЛАССЫ (сгенерировано GameScript)
// ========================================

class Hero : public Entity {
public:
    void on_create() {
        this->name = "Герой";
        this->hp = 100;
    }

};

class Main : public System {
public:
    std::string hero_name;
    int hero_hp;
    int hero_x;
    int gold;

    Main() : hero_name(""), hero_hp(0), hero_x(0), gold(0) {}

    void on_start() {
        this->hero_name = "Герой";
        this->hero_hp = 100;
        this->hero_x = 400;
        this->gold = 0;
        std::cout << "Game started!" << std::endl;
    }

    void on_update() {
        this->gold = this->gold + 1;
        this->hero_x = this->hero_x + 1;
        if (this->hero_x > 800) {
            this->hero_x = 0;
        }
    }

};

int main() {
    Main main;
    main.hero_name = "Герой";
    main.hero_hp = 100;
    main.hero_x = 400;
    main.gold = 0;
    std::cout << "Game started!" << std::endl;
    main.gold = main.gold + 1;
    main.hero_x = main.hero_x + 1;
    if (main.hero_x > 800) {
        main.hero_x = 0;
    }
    return 0;
}