# GameScript
![License](https://img.shields.io/github/license/become-a-human/gamescript)
![Version](https://img.shields.io/badge/version-0.4.3-orange)
![PyVer](https://img.shields.io/badge/python-3.9+-blue)
![Output](https://img.shields.io/badge/output-C++-00599C)

DSL для геймдева, компилируется в C++. Пиши как на Python, работает как C++.

>⚠️ <strong>v0.4.3</strong> — активная разработка.

## Быстрый старт
```
pip install -e .
gamescript --version
```

## Пример
### hero.gs
```
# --header
@load "entity"
HERO = { "name": "Артур", "hp": 100 }

class Hero(Entity):
def on_create(self):
self.hp = HERO.hp
self:set_animation("idle", 4, 10)

def take_damage(self, amount: int):
    self.hp = self.hp - amount
    if self.hp <= 0:
        self.is_alive = false
```

### hero.h (сгенерированный заголовок)
```
#pragma once
#include "entity.h"
struct HERO_t { std::string name; int hp; };
const HERO_t HERO = { .name = "Артур", .hp = 100 };


class Hero : public Entity {
    public:
    void on_create();
    void take_damage(int amount);
};
```

## Возможности
- Автовывод типов
- Раздельная компиляция (# --header)
- Прямая компиляция (--build)

## Структура проекта
```
gamescript/
    ├── gamescript/          # компилятор
    │   ├── tokens.py
    │   ├── lexer.py
    │   ├── ast_nodes.py
    │   ├── parser.py
    │   ├── codegen_cpp.py
    │   └── compiler.py
    ├── examples/            # примеры
    │   ├── entity.gs        # базовый класс
    │   ├── system.gs        # базовый класс
    │   ├── joystick.gs      # джойстик
    │   ├── hero.gs          # герой
    │   └── __main__.gs      # точка входа
    ├── tests/
    ├── Makefile
    ├── setup.py
    ├── CHANGELOG.md
    ├── LICENSE
    └── README.md
```

## Использование
```
gamescript hero.gs                     # в консоль
gamescript hero.gs hero.h              # заголовок
gamescript __main__.gs --build -o game # прямая компиляция в бинарник

from gamescript import compile_file, compile_text
cpp = compile_text('HERO = { "hp": 100 }')
compile_file("main.gs", build=True)
```
