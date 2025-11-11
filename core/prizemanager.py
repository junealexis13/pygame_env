import sqlite3
import os

class PrizeManager:
    def __init__(self, db_path=os.path.join('db','prizes.db'), initial_prizes=None):
        self.db_path = db_path
        self.prizes = {}
        

        # Load existing prizes from database
        self.load_prizes()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prizes
                (name TEXT PRIMARY KEY, count INTEGER)
            ''')

            conn.commit()

    def load_prizes(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name, count FROM prizes')
            for name, quantity in cursor.fetchall():
                self.prizes[name] = quantity

    def initialize_prizes(self):
        self.load_prizes()

    def save_prizes(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for name, quantity in self.prizes.items():
                cursor.execute('''
                    UPDATE prizes SET count = ? WHERE name = ?
                ''', (quantity, name))
            conn.commit()

    def get_prize_count(self, prize_name):
        return self.prizes.get(prize_name, 0)

    def decrement_prize(self, prize_name):
        if prize_name in self.prizes and self.prizes[prize_name] > 0:
            self.prizes[prize_name] -= 1
            self.save_prizes()
            return True
        return False

    def close(self):
        self.save_prizes()