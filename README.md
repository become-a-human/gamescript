<h1>GameScript</h1>

<p>DSL для геймдева, компилируется в C++. Пиши как на Python, работает как C++.</p>

<blockquote>
⚠️ <strong>Ранняя версия (v0.1.0).</strong> Многие возможности ещё в разработке.
Не рекомендуется для production-проектов. Используй на свой страх и риск.
</blockquote>

<h2>Как это работает</h2>

<p>GameScript читает <code>.gs</code> файлы, парсит их, разрешает импорты (<code>@load</code>, <code>~grab</code>, <code>&link</code>) и генерирует C++ код.</p>

<h2>Пример</h2>

<h3>hero.gs</h3>

<pre><code>HERO = {
    "name": str("Артур"),
    "hp": int(100),
    "max_hp": int(100),
    "speed": float(1.5),
    "is_alive": bool(true),
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

<h3>Сгенерированный C++</h3>

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
    void on_create() {
        this->hp = HERO.max_hp;
        this->is_alive = true;
    }
    
    void take_damage(int amount) {
        this->hp = this->hp - amount;
        if (this->hp <= 0) {
            this->is_alive = false;
        }
    }
};
</code></pre>

<h2>Что уже работает</h2>

<ul>
    <li>Словари → C++ struct</li>
    <li>Классы с наследованием</li>
    <li>Методы с типизированными параметрами (<code>int</code>, <code>str</code>, <code>float</code>, <code>bool</code>)</li>
    <li><code>if</code>/<code>else</code>, <code>while</code>, <code>for</code>, <code>continue</code>, <code>break</code></li>
    <li>Операторы: <code>+</code>, <code>-</code>, <code>*</code>, <code>/</code>, <code>=</code>, <code>+=</code>, <code>-=</code>, <code>*=</code>, <code>/=</code></li>
    <li>Сравнения: <code>==</code>, <code>!=</code>, <code>&lt;</code>, <code>&gt;</code>, <code>&lt;=</code>, <code>&gt;=</code></li>
    <li>Вызов методов через <code>:</code></li>
    <li>Док-строки: <code>"""описание"""</code> или <code>'''описание'''</code></li>
    <li>Умные <code>#include</code> (только нужные)</li>
</ul>

<h2>Чего ещё нет (в планах)</h2>

<ul>
    <li>Раздельная компиляция (каждый .gs → свой .h/.cpp)</li>
    <li>Массивы и словари как полноценные типы в методах</li>
    <li>Строковые операции</li>
    <li>Импорт стандартной библиотеки</li>
    <li>Оптимизация кодгена</li>
    <li>Поддержка Android/iOS из коробки</li>
</ul>

<h2>Система импортов</h2>

<table border="1">
    <tr><th>Команда</th><th>Пример</th><th>Описание</th></tr>
    <tr><td><code>@load</code></td><td><code>@load "hero.gs"</code></td><td>Импорт всего файла</td></tr>
    <tr><td><code>@load?</code></td><td><code>@load? "plugin.gs"</code></td><td>Опциональный импорт</td></tr>
    <tr><td><code>@load like</code></td><td><code>@load "hero" like "Player"</code></td><td>Импорт с переименованием</td></tr>
    <tr><td><code>~grab</code></td><td><code>~grab &lt;Hero&gt;</code></td><td>Захват класса/словаря</td></tr>
    <tr><td><code>~grab like</code></td><td><code>~grab &lt;Hero&gt; like &lt;Player&gt;</code></td><td>Захват с переименованием</td></tr>
    <tr><td><code>&link</code></td><td><code>&link &lt;on_create&gt;</code></td><td>Захват функции</td></tr>
    <tr><td><code>&link like</code></td><td><code>&link &lt;on_create&gt; like &lt;init&gt;</code></td><td>Захват функции с переименованием</td></tr>
</table>

<h2>Установка</h2>

<pre><code>git clone https://github.com/become-a-human/gamescript.git
cd gamescript
pip install -e .
</code></pre>

<h2>Использование</h2>

<pre><code># Компиляция
gamescript hero.gs                    # вывод в консоль
gamescript hero.gs hero.cpp           # в файл

# Python API
from gamescript import compile_file, compile_text

cpp = compile_text('HERO = { "hp": int(100) }')
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
├── examples/            # Примеры на GameScript
│   ├── hero.gs
│   ├── weapons.gs
│   ├── enemies.gs
│   ├── inventory.gs
│   ├── equipment.gs
│   ├── maps.gs
│   └── full_game.gs
├── tests/               # Тесты
│   ├── test_lexer.py
│   ├── test_parser.py
│   └── test_compiler.py
├── Makefile
├── setup.py
├── LICENSE
└── README.md
</code></pre>

<h2>Ссылки</h2>

<ul>
    <li><a href="https://t.me/kraudov">Telegram</a></li>
    <li><a href="https://github.com/become-a-human/gamescript/issues">Баг-репорты и предложения</a></li>
</ul>

<h2>Лицензия</h2>

<p><a href="LICENSE">WTFPL</a> — делай что хочешь.</p>
