#include <sqlite3.h>
#include <string>

extern "C" {
    sqlite3* db_open(const char* path) {
        sqlite3* db;
        sqlite3_open(path, &db);
        return db;
    }
    
    const char* db_exec(sqlite3* db, const char* sql) {
        static std::string result;
        result.clear();
        char* err = nullptr;
        sqlite3_exec(db, sql, nullptr, nullptr, &err);
        if (err) { result = err; sqlite3_free(err); }
        else result = "OK";
        return result.c_str();
    }
    
    void db_close(sqlite3* db) {
        sqlite3_close(db);
    }
}
