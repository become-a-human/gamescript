<h1>GameScript</h1>

<a href="https://github.com/become-a-human/gamescript"><img src="https://img.shields.io/github/license/become-a-human/gamescript"/></a> <a href="https://github.com/become-a-human/gamescript"><img src="https://img.shields.io/badge/version-0.4.0-orange"/></a> <img src="https://img.shields.io/badge/python-3.9+-blue"/> <img src="https://img.shields.io/badge/output-C++-00599C"/>

<p>DSL для геймдева, компилируется в C++. Пиши как на Python, работает как C++.</p>

<blockquote>
⚠️ <strong>Ранняя версия (v0.4.0).</strong> Активная разработка. API может меняться.
</blockquote>

<h2>Как это работает</h2>

<h2>Пример</h2>
<h3>hero.gs</h3>
<pre><code># --header
HERO = {
    "name": "Артур",
    "hp": 100,
    "speed": 1.5,
}

class Hero(Entity):
    def on_create(self):
        self.hp = HERO.hp
        self:set_animation("idle", 4, 10)
    
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
};
const HERO_t HERO = { .name = "Артур", .hp = 100, .speed = 1.5f };

class Hero : public Entity {
public:
    void on_create();
    void take_damage(int amount);
};
</code></pre>

<h2>Возможности</h2>
<ul>
    <li>Словари → C++ struct</li>
    <li>Классы с наследованием, перегрузка методов</li>
    <li>Автовывод типов</li>
    <li>Раздельная компиляция (<code># --header</code>)</li>
    <li><code>@load</code> → <code>#include</code></li>
    <li><code>__main__.gs</code> → <code>int main()</code></li>
    <li>Анимации, джойстик</li>
    <li><code>if</code>/<code>elif</code>/<code>else</code>, <code>while</code>, <code>for</code></li>
    <li>Операторы: <code>++</code>, <code>--</code>, <code>+=</code>, <code>and</code>, <code>or</code>, <code>not</code></li>
    <li><code>print()</code>, <code>assert</code></li>
    <li><code>--build</code> — бинарник</li>
</ul>

<h2>Установка</h2>
<pre><code>git clone https://github.com/become-a-human/gamescript.git
cd gamescript
pip install -e .
</code></pre>

<h2>Использование</h2>
<pre><code>gamescript hero.gs                  # в консоль
gamescript hero.gs hero.h           # заголовок
gamescript __main__.gs --build      # бинарник

from gamescript import compile_file, compile_text
cpp = compile_text('HERO = { "hp": 100 }')
compile_file("hero.gs", "hero.h")
compile_file("__main__.gs", build=True)
</code></pre>

<h2>Ссылки</h2>
<ul>
    <li><a href="https://t.me/kraudov">Telegram</a></li>
    <li><a href="https://github.com/become-a-human/gamescript/issues">Баг-репорты</a></li>
</ul>

<h2>Лицензия</h2>
<p><a href="LICENSE">WTFPL</a> — делай что хочешь.</p>