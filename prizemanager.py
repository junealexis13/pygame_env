import sqlite3

class PrizeManager:
    def __init__(self, db_path="prizes.db", initial_prizes=None):
        self.conn = sqlite3.connect(db_path)
        self.create_prize_table(initial_prizes or [])

    def create_prize_table(self, prizes):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prizes (
                name TEXT PRIMARY KEY,
                count INTEGER
            )
        """)
        for prize, count in prizes.items():
            cursor.execute("INSERT OR IGNORE INTO prizes (name, count) VALUES (?, ?)", (prize, count))
        self.conn.commit()

    def get_prize_count(self, prize_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT count FROM prizes WHERE name = ?", (prize_name,))
        result = cursor.fetchone()
        return result[0] if result else 0

    def decrement_prize(self, prize_name):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE prizes SET count = count - 1 WHERE name = ? AND count > 0", (prize_name,))
        self.conn.commit()

    def prizes_available(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(count) FROM prizes")
        result = cursor.fetchone()
        return result[0] > 0 if result else False

    def close(self):
        self.conn.close()