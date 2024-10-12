import sqlite3


class UserDatabase: 
    def __init__(self, db_name):
        self.db_name = db_name
        self.db = None
        self.cursor = None
    
    def connect(self):
        self.db = sqlite3.connect(self.db_name)
        self.cursor = self.db.cursor()

    def create_table_user(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users( 
            id_owner INTEGER,
            id INTEGER,
            referals INTEGER,
            balance INTEGER
        )""")
        self.db.commit()
    

    def create_users_ref_in_db(self,ref_id,id):
        self.cursor.execute("""INSERT OR IGNORE INTO users (id_owner, id, referals, balance)
                       VALUES (?, ?, ?, ?)""",
                    (ref_id, id,  0, 0))
        self.db.commit()
    
    def get_info_for_db(self,id):
        result = self.cursor.execute("SELECT * FROM users WHERE id = ?",(id,)).fetchall()
        if result:
            return result
        else:
            return None


    def add_info_ref_balance(self,id):
        balance = self.cursor.execute('SELECT balance FROM users WHERE id = ?',(id,)).fetchone()[0]
        referals = self.cursor.execute('SELECT referals FROM users WHERE id = ?',(id,)).fetchone()[0]

        self.cursor.execute(f'UPDATE users SET referals = {referals+1} WHERE id = ?',(id,))
        self.cursor.execute(f'UPDATE users SET balance = {balance+10} WHERE id = ?',(id,))
        self.db.commit()



    def close(self):
        self.cursor.close()
        self.db.close()