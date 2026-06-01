PYTHONWARNINGS=ignore
NAME = game

.PHONY: install test test-lexer test-parser test-compiler compile build clean

# Установка
install:
	pip install -e .

# Все тесты
test:
	@echo "=== Лексер ==="
	python tests/test_lexer.py
	@echo ""
	@echo "=== Парсер ==="
	python tests/test_parser.py
	@echo ""
	@echo "=== Компилятор ==="
	python tests/test_compiler.py
	@echo ""
	@echo "✓ Все тесты пройдены!"

# Тесты по отдельности
test-lexer:
	python tests/test_lexer.py

test-parser:
	python tests/test_parser.py

test-compiler:
	python tests/test_compiler.py

# Компиляция примеров (только .h и .cpp, без сборки)
compile:
	@mkdir -p examples/generated
	python -m gamescript.compiler examples/entity.gs examples/generated/entity.h
	python -m gamescript.compiler examples/system.gs examples/generated/system.h
	python -m gamescript.compiler examples/joystick.gs examples/generated/joystick.h
	python -m gamescript.compiler examples/screen.gs examples/generated/screen.h
	python -m gamescript.compiler examples/rng.gs examples/generated/rng.h
	python -m gamescript.compiler examples/calculator.gs examples/generated/calculator.h
	python -m gamescript.compiler examples/clock.gs examples/generated/clock.h
	python -m gamescript.compiler examples/aabb.gs examples/generated/aabb.h
	python -m gamescript.compiler examples/sound.gs examples/generated/sound.h
	python -m gamescript.compiler examples/network.gs examples/generated/network.h
	python -m gamescript.compiler examples/database.gs examples/generated/database.h
	python -m gamescript.compiler examples/thread.gs examples/generated/thread.h
	python -m gamescript.compiler examples/menu.gs examples/generated/menu.h
	python -m gamescript.compiler examples/hero.gs examples/generated/hero.h
	python -m gamescript.compiler examples/__main__.gs examples/generated/__main__.cpp

# Полная сборка (скомпоновать в бинарник)
build:
	@mkdir -p examples/generated
	python -m gamescript.compiler examples/__main__.gs examples/generated/__main__.cpp --build -o $(NAME)

# Очистка
clean:
	rm -rf examples/generated/
	rm -rf *.egg-info
	@echo "✓ Очищено"