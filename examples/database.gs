# --header
@load "sqlite"

class Database(System):
    def connect(self, path: str):
        self.db = db_open(path)
    
    def query(self, sql: str):
        self.result = db_exec(self.db, sql)
    
    def disconnect(self):
        db_close(self.db)
