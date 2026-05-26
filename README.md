<h1>GameScript</h1>

<a href="https://github.com/become-a-human/gamescript"><img src="https://img.shields.io/github/license/become-a-human/gamescript"/></a> <a href="https://github.com/become-a-human/gamescript"><img src="https://img.shields.io/badge/version-0.2.0-orange"/></a> <img src="https://img.shields.io/badge/python-3.9+-blue"/> <img src="https://img.shields.io/badge/output-C++-00599C"/>

<p>DSL для геймдева, компилируется в C++. Пиши как на Python, работает как C++.</p>

<blockquote>
⚠️ <strong>Ранняя версия (v0.2.0).</strong> Активная разработка. API может меняться.
</blockquote>

<h2>Как это работает</h2>

<p>GameScript читает <code>.gs</code> файлы, парсит их и генерирует C++ код.
<code># --header</code> → заголовочный файл (<code>.h</code>), без неё → <code>.cpp</code>.
<code>@load</code> превращается в <code>#include</code>.</p>

<h2>Пример</h2>

<h3>hero.gs (с # --header)</h3>

<pre><code># --header
# ===== ГЕРОЙ =====
HERO = {
    "name": "Артур",
    "hp": 100,
    "max_hp": 100,
    "speed": 1.5,
    "is_alive": true,
}

class Hero(Entity):
    """Главный герой"""
    
    def on_create(self):
        self.hp = HERO.max_hp
        self.is_alive = true
    
    def take_damage(self, amount: int):
        self.hp = self.hp - amount
        if self.hp <= 0:
            self.is_alive = false
</code></pre>

<h3>Сгенерированный hero.h</h3>

<pre><code>struct HERO_t {
    std::string name;
    int hp;
    int max_hp;
    float speed;
    bool is_alive;
};

const HERO_t HERO = {
    .name = "Артур",
    .hp = 100,
    .max_hp = 100,
    .speed = 1.5f,
    .is_alive = true,
};

class Hero : public Entity {
public:
    int hp;
    bool is_alive;
    
    void on_create();
    void take_damage(int amount);
};
</code></pre>

<h2>Что уже работает в v0.2.0</h2>

<ul>
    <li><strong>Автовывод типов</strong> — <code>100</code>, <code>"текст"</code>, <code>true</code> без <code>int()</code>, <code>str()</code></li>
    <li><strong>Словари → C++ struct</strong> с авто-типами</li>
    <li><strong>Классы с наследованием</strong> + авто-поля из методов</li>
    <li><strong>Раздельная компиляция</strong> — <code># --header</code> → <code>.h</code>, иначе <code>.cpp</code></li>
    <li><strong>@load → #include</strong> — правильные зависимости между файлами</li>
    <li><strong>Импорт Python-библиотек</strong> — <code>@load "math"</code> → <code>#include &lt;cmath&gt;</code></li>
    <li><strong>Рантайм</strong> — <code>Entity</code> и <code>System</code> генерируются автоматически</li>
    <li><code>if</code>/<code>else</code>, <code>while</code>, <code>for</code>, <code>continue</code>, <code>break</code></li>
    <li>Операторы: <code>+</code>, <code>-</code>, <code>*</code>, <code>/</code>, <code>=</code>, <code>+=</code>, <code>-=</code>, <code>*=</code>, <code>/=</code></li>
    <li>Сравнения: <code>==</code>, <code>!=</code>, <code>&lt;</code>, <code>&gt;</code>, <code>&lt;=</code>, <code>&gt;=</code></li>
    <li>Вызов методов через <code>:</code></li>
    <li>Док-строки: <code>"""описание"""</code></li>
</ul>

<h2>Что нового в v0.2.0</h2>

<ul>
    <li>✅ Автовывод типов — больше не нужны <code>int()</code>, <code>str()</code>, <code>bool()</code></li>
    <li>✅ Раздельная компиляция с <code># --header</code></li>
    <li>✅ <code>@load</code> → <code>#include</code> (не встраивает код)</li>
    <li>✅ Авто-поля классов из <code>self.xxx = ...</code></li>
    <li>✅ Рантайм <code>Entity</code> и <code>System</code></li>
    <li>✅ Импорт стандартных библиотек</li>
</ul>

<h2>В планах (v0.3.0+)</h2>

<ul>
    <li>Компиляция в бинарник (<code>--build</code>)</li>
    <li>Массивы и словари как полноценные типы в методах</li>
    <li>Строковые операции</li>
    <li>Цикл <code>for</code> с диапазоном (<code>for i in 0..10</code>)</li>
    <li><code>switch</code>/<code>case</code></li>
    <li>Модули: <code>import</code> вместо <code>@load</code></li>
    <li>Дебаг-режим с картой исходников</li>
    <li>Оптимизация кодгена</li>
    <li>Больше примеров: джойстик, инвентарь, диалоги</li>
</ul>

<h2>Система импортов</h2>

<table border="1">
    <tr><th>Команда</th><th>Пример</th><th>C++ вывод</th></tr>
    <tr><td><code>@load</code></td><td><code>@load "hero"</code></td><td><code>#include "hero.h"</code></td></tr>
    <tr><td><code>@load?</code></td><td><code>@load? "plugin"</code></td><td>Опциональный</td></tr>
    <tr><td><code>@load like</code></td><td><code>@load "math" like "Math"</code></td><td><code>#include &lt;cmath&gt;</code> + namespace</td></tr>
    <tr><td><code>~grab</code></td><td><code>~grab &lt;Hero&gt;</code></td><td><code>using Hero;</code></td></tr>
    <tr><td><code>~grab like</code></td><td><code>~grab &lt;Hero&gt; like &lt;Player&gt;</code></td><td><code>using Player = Hero;</code></td></tr>
    <tr><td><code>&link</code></td><td><code>&link &lt;on_create&gt;</code></td><td>Захват функции</td></tr>
</table>

<h2>Установка</h2>

<pre><code>git clone https://github.com/become-a-human/gamescript.git
cd gamescript
pip install -e .
</code></pre>

<h2>Использование</h2>

<pre><code># Компиляция
gamescript hero.gs                    # вывод в консоль
gamescript hero.gs hero.h             # в файл

# Python API
from gamescript import compile_file, compile_text

cpp = compile_text('HERO = { "hp": 100 }')
compile_file("game.gs", "output.cpp")

# Тесты
make test      # все тесты
make compile   # компиляция примеров
</code></pre>

<h2>Структура проекта</h2>

<pre><code>gamescript/
├── gamescript/          # Компилятор
│   ├── __init__.py
│   ├── tokens.py        # Типы токенов
│   ├── lexer.py         # Лексер
│   ├── ast_nodes.py     # Узлы AST
│   ├── parser.py        # Парсер
│   ├── codegen_cpp.py   # Генератор C++
│   └── compiler.py      # Главный модуль
├── runtime/             # Рантайм
│   └── runtime.h        # Entity, System
├── examples/            # Примеры на GameScript
│   ├── hero.gs
│   ├── weapons.gs
│   ├── enemies.gs
│   ├── inventory.gs
│   ├── equipment.gs
│   └── mainfile.gs
├── tests/               # Тесты
│   ├── test_lexer.py
│   ├── test_parser.py
│   └── test_compiler.py
├── Makefile
├── setup.py
├── CHANGELOG.md
├── LICENSE
└── README.md
</code></pre>

<h2>Ссылки</h2>

<ul>
    <li><a href="https://t.me/kraudov">Telegram</a></li>
    <li><a href="https://github.com/become-a-human/gamescript/issues">Баг-репорты</a></li>
</ul>

<h2>Лицензия</h2>

<p><a href="LICENSE">WTFPL</a> — делай что хочешь.</p>