PYTHONWARNINGS=ignore

.PHONY: install test test-lexer test-parser test-compiler test-full compile build clean

install:
	pip install -e .

test:
	@echo "=== Лексер ==="
	python tests/test_lexer.py
	@echo "=== Парсер ==="
	python tests/test_parser.py
	@echo "=== Компилятор ==="
	python tests/test_compiler.py
	@echo "=== Полный тест ==="
	python tests/test_full.py
	@echo "✓ Все тесты пройдены!"

test-lexer:
	python tests/test_lexer.py

test-parser:
	python tests/test_parser.py

test-compiler:
	python tests/test_compiler.py

test-full:
	python tests/test_full.py

compile:
	@mkdir -p examples/generated
	python -m gamescript.compiler examples/entity.gs examples/generated/entity.h
	python -m gamescript.compiler examples/system.gs examples/generated/system.h
	python -m gamescript.compiler examples/enemy.gs examples/generated/enemy.h
	python -m gamescript.compiler examples/hero.gs examples/generated/hero.h
	python -m gamescript.compiler examples/__main__.gs examples/generated/__main__.cpp

build:
	@mkdir -p examples/generated
	python -m gamescript.compiler examples/__main__.gs examples/generated/__main__.cpp --build -o game

clean:
	rm -rf examples/generated/
	rm -rf *.egg-info
	@echo "✓ Очищено"

editor:
	@mkdir -p examples/generated
	python -m gamescript.compiler examples/editor.gs examples/generated/editor.cpp --build -o gs_editor