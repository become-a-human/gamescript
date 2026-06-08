#pragma once
#include <string>

void ncurses_init();
void ncurses_end();
void ncurses_clear();
void ncurses_refresh();
int ncurses_getch();
void ncurses_print(int y, int x, const std::string& text);
void ncurses_status(const std::string& text);
std::string read_file(const std::string& path);
void write_file(const std::string& path, const std::string& content);
int gs_len(const std::string& s);
std::string gs_substr(const std::string& s, int start, int len);
