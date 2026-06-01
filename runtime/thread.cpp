#include <thread>
#include <functional>
#include <chrono>

extern "C" {
    void thread_sleep(int ms) {
        std::this_thread::sleep_for(std::chrono::milliseconds(ms));
    }
    
    // Для запуска функции в отдельном потоке нужно лямбды, но в GameScript они уже есть
}
