<h1>GameScript</h1>

<a href="https://github.com/become-a-human/gamescript"><img src="https://img.shields.io/github/license/become-a-human/gamescript"/></a> <a href="https://github.com/become-a-human/gamescript"><img src="https://img.shields.io/badge/version-0.3.0-orange"/></a> <img src="https://img.shields.io/badge/python-3.9+-blue"/> <img src="https://img.shields.io/badge/output-C++-00599C"/>

<p>DSL для геймдева, компилируется в C++. Пиши как на Python, работает как C++.</p>

<blockquote>
⚠️ <strong>Ранняя версия (v0.3.0).</strong> Активная разработка. API может меняться.
</blockquote>

<h2>Как это работает</h2>

<p>GameScript читает <code>.gs</code> файлы, парсит их и генерирует C++ код.
<code># --header</code> → заголовочный файл (<code>.h</code>), без неё → <code>.cpp</code>.
<code>@load</code> превращается в <code>#include</code>.
<code>--build</code> компилирует сразу в бинарник.</p>

<h2>Пример</h2>

<h3>hero.gs (с # --header)</h3>

<pre><code># --header
HERO = {
    "name": "Артур",
    "hp": 100,
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
    float speed;
    bool is_alive;
};

const HERO_t HERO = {
    .name = "Артур",
    .hp = 100,
    .speed = 1.5f,
    .is_alive = true,
};

class Hero : public Entity {
public:
    void on_create();
    void take_damage(int amount);
};
</code></pre>

<h2>Что уже работает</h2>

<ul>
    <li><strong>Автовывод типов</strong> — <code>100</code>, <code>"текст"</code>, <code>true</code>, <code>None</code></li>
    <li><strong>Словари → C++ struct</strong> с авто-типами</li>
    <li><strong>Классы с наследованием</strong> + авто-поля + конструкторы</li>
    <li><strong>Раздельная компиляция</strong> — <code># --header</code> → <code>.h</code>, иначе <code>.cpp</code></li>
    <li><strong>@load → #include</strong> — правильные зависимости</li>
    <li><strong>Импорт библиотек</strong> — <code>@load "math"</code>, <code>@load "sdl2"</code></li>
    <li><strong>Runtime auto-gen</strong> — <code>Entity</code> и <code>System</code> создаются автоматически</li>
    <li><strong>--build</strong> — компиляция в бинарник</li>
    <li><code>if</code>/<code>else</code>, <code>while</code>, <code>for</code>, <code>continue</code>, <code>break</code></li>
    <li>Операторы: <code>+</code>, <code>-</code>, <code>*</code>, <code>/</code>, <code>=</code>, <code>+=</code>, <code>-=</code></li>
    <li>Сравнения: <code>==</code>, <code>!=</code>, <code>&lt;</code>, <code>&gt;</code>, <code>&lt;=</code>, <code>&gt;=</code></li>
    <li>Вызов методов через <code>:</code></li>
    <li>Док-строки: <code>"""описание"""</code></li>
</ul>

<h2>Что нового в v0.3.0</h2>

<ul>
    <li>✅ Автовывод типов: <code>int</code>, <code>float</code>, <code>str</code>, <code>bool</code>, <code>null</code></li>
    <li>✅ Конструкторы с авто-инициализацией</li>
    <li>✅ Наследование полей от родителей</li>
    <li>✅ <code>--build</code> — компиляция в бинарник</li>
    <li>✅ Runtime auto-gen без хардкода</li>
    <li>✅ Поддержка SDL2</li>
</ul>

<h2>В планах (v0.4.0+)</h2>

<ul>
    <li>Entity и System как .gs файлы (не хардкод)</li>
    <li>Массивы и словари в методах</li>
    <li>Строковые операции</li>
    <li>Джойстик для мобилок</li>
    <li>Дебаг-режим</li>
</ul>

<h2>Установка</h2>

<pre><code>git clone https://github.com/become-a-human/gamescript.git
cd gamescript
pip install -e .
</code></pre>

<h2>Использование</h2>

<pre><code class="bash">
# Компиляция
gamescript hero.gs                     # в консоль
gamescript hero.gs hero.h              # заголовок
gamescript mainfile.gs --build         # бинарник
</code></pre>

<pre><code class="python">
# Python API
from gamescript import compile_file, compile_text

# Компиляция строки в C++
cpp = compile_text('HERO = { "hp": 100 }')

# Компиляция файла
compile_file("hero.gs", "hero.h")      # заголовок
compile_file("mainfile.gs", "main.cpp") # реализация
compile_file("mainfile.gs", build=True) # сразу бинарник
</code></pre>

<pre><code class="bash">
# Тесты
make test      # все тесты
make compile   # генерация .h/.cpp
make build     # бинарник
</code></pre>

<h2>Ссылки</h2>

<ul>
    <li><a href="https://t.me/kraudov">Telegram</a></li>
    <li><a href="https://github.com/become-a-human/gamescript/issues">Баг-репорты / Предложения</a></li>
</ul>

<h2>Лицензия</h2>

<p><a href="LICENSE">WTFPL</a> — делай что хочешь.</p>