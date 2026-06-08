#include <ncurses.h>
#include <string>
#include <fstream>

static WINDOW* gs_win = nullptr;

void ncurses_init() {
    gs_win = initscr();
    noecho();
    cbreak();
    keypad(gs_win, TRUE);
}

void ncurses_end() {
    if (gs_win) endwin();
    gs_win = nullptr;
}

void ncurses_clear() { if (gs_win) werase(gs_win); }
void ncurses_refresh() { if (gs_win) wrefresh(gs_win); }
int ncurses_getch() { return gs_win ? wgetch(gs_win) : -1; }

void ncurses_print(int y, int x, const std::string& text) {
    if (gs_win) mvwprintw(gs_win, y, x, "%s", text.c_str());
}

void ncurses_status(const std::string& text) {
    if (gs_win) {
        wattron(gs_win, A_REVERSE);
        mvwprintw(gs_win, 0, 0, "%s", text.c_str());
        wattroff(gs_win, A_REVERSE);
    }
}

std::string read_file(const std::string& path) {
    std::ifstream f(path);
    std::string content, line;
    while (std::getline(f, line)) content += line + '\n';
    return content;
}

void write_file(const std::string& path, const std::string& content) {
    std::ofstream f(path);
    f << content;
}

int gs_len(const std::string& s) { return s.length(); }

std::string gs_substr(const std::string& s, int start, int len) {
    return s.substr(start, len);
}
