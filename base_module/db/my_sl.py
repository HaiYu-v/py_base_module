import sqlite3


class SL:
    @staticmethod
    def get_conn(db_path: str) -> sqlite3.Connection:
        conn = sqlite3.connect(
            db_path,
            timeout=10,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row

        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")

        return conn