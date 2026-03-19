import sqlite3
import uuid
from base_module import BaseMS
from base_module import SqlUtil

class SlUtil:


    @staticmethod
    def insert_sql(table: str, fields: list[str], replace: bool = False) -> str:
        """
        生成 SQLite 插入 SQL，可选冲突更新
        :param table: 表名
        :param fields: 列名列表
        :return: INSERT SQL 字符串
        """
        cols = ", ".join(f'"{c}"' for c in fields)  # SQLite 支持双引号
        placeholders = ", ".join(["?"] * len(fields))


        sql = f"INSERT {'OR REPLACE' if replace else ''} INTO {table} ({cols}) VALUES ({placeholders})"
        return sql


    @staticmethod
    def insert(db: sqlite3.Connection, table: str, fields: list[str], data: list[list], replace:bool = False):
        """
        批量插入数据
        """
        if not fields:
            raise Exception("字段列表不能为空")
        if not data:
            return

        col_num = len(fields)
        for i, cur in enumerate(data):
            if len(cur) != col_num:
                raise ValueError(f"第 {i} 行数据列数 {len(cur)} 与字段数 {col_num} 不一致")

        sql = SlUtil.insert_sql(table, fields, replace)
        # SQLite 批量插入用 executemany
        with db:
            db.executemany(sql, data)

    @staticmethod
    def insert_dict(db: sqlite3.Connection, table: str, data: list[dict[str, any]], replace:bool = False):
        """
        插入字典形式的数据
        """
        if not data:
            return

        col_num = 0
        for i, cur in enumerate(data):
            if col_num == 0:
                col_num = len(cur.keys())
            if len(cur.keys()) != col_num:
                raise ValueError(f"第 {i} 行数据列数 {len(cur)} 与字段数 {col_num} 不一致")

        fields = list(data[0].keys())
        insert_data = [[d[f] for f in fields] for d in data]
        SlUtil.insert(db, table, fields, insert_data, replace)
