from dataclasses import fields
from operator import is_
from re import M
import uuid
from base_module import BaseMS
from base_module import SqlUtil
from base_module.info.log import Log

class MsUtil(object):
    # 禁止插入
    FORBID_INSERT = False
    """ -------------------------------------------------------------------
     * 生成 ON DUPLICATE KEY UPDATE 语句
     * 只在字段值不同的时候才更新
     * @Prams fields: 要更新的字段名列表
    """
    @staticmethod
    def duplicate(fields: list[str]) -> str:
        updates = ",\n".join(
            f"{field} = VALUES({field})"
            for field in fields
        )
        sql = f"ON DUPLICATE KEY UPDATE\n{updates}"
        return sql

    """ -------------------------------------------------------------------
     * 生成插入sql
     * @Prams table: 表名
     * @Prams fields: 列名列表
    """
    @staticmethod
    def insert_sql(table: str, fields: list[str], is_ignore = False, duplicate:list[str]=[]) -> str:
        """
        生成 MySQL 插入 SQL
        :param table: 表名
        :param fields: 列名列表
        :return: INSERT SQL 字符串
        """
        cols = ", ".join(f"`{c}`" for c in fields)
        placeholders = ", ".join(["%s"] * len(fields))

        duplicate_sql = ''
        if len(duplicate) > 0:
            is_ignore = True
            duplicate_sql = MsUtil.duplicate(duplicate)
        sql = f"INSERT {'IGNORE' if is_ignore else ''} INTO {table} ({cols}) VALUES ({placeholders}) {duplicate_sql}"
        return sql

    @staticmethod
    def insert_temporary_table(db:BaseMS, data:list[list], fields:list[tuple[str, str]],batch_size=1000) -> str:
        table = f"temporary_{uuid.uuid4().hex}"
        fields_sql = SqlUtil.create_fields(fields)

        sql = f"CREATE TEMPORARY TABLE {table} {fields_sql} "
        db.execute(sql)

        fields = [field[0] for field in fields]
        MsUtil.check(fields,data)
        sql = MsUtil.insert_sql(table, fields)
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            db.execute(sql, batch)
        return table

    @staticmethod
    def check(fields: list[str], data: list[list]):
        if not fields or len(fields) == 0:
            raise Exception("字段列表不能为空")

        if not data or len(data) == 0 :
            return

        col_num = len(fields)
        for i, cur in enumerate(data):
            if len(cur) != col_num:
                raise ValueError(f"第 {i} 行数据列数 {len(cur)} 与字段数 {col_num} 不一致")

    @staticmethod
    def insert(db:BaseMS, table: str, fields: list[str], data: list[list], is_ignore = False, duplicate:list[str]=[],batch_size=1000):
        MsUtil.check(fields,data)
        sql = MsUtil.insert_sql(table, fields,is_ignore,duplicate)
        if not MsUtil.FORBID_INSERT:
            insert_total = 0
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                db.execute(sql, batch)
                insert_total += len(batch)
                Log.log(f">>>>>> {table} 已插入{insert_total}")

    

    @staticmethod
    def insert_dict(db:BaseMS, table: str,data: list[dict[str, any]], is_ignore = False, duplicate:list[str]=[],batch_size=1_000):
        if not data or len(data) == 0 :
            return

        col_num = 0
        for i, cur in enumerate(data):
            if col_num == 0:
                col_num = len(cur.keys())
            if len(cur.keys()) != col_num:
                raise ValueError(f"第 {i} 行数据列数 {len(cur)} 与字段数 {col_num} 不一致")

        fields = list(data[0].keys())
        insert_data = [[d[f] for f in fields] for d in data]
        MsUtil.insert(db, table, fields, insert_data,is_ignore,duplicate,batch_size)

    @staticmethod
    def update_sql(table: str, fields: list[str], where_fields: list[str]) -> str:
        set_clause = ", ".join(f"`{f}` = %s" for f in fields)
        where_clause = " AND ".join(f"`{f}` = %s" for f in where_fields)
        return f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

    @staticmethod
    def update(db: BaseMS, table: str, data: list[list], set_fields: list[str], where_fields: list[str], batch_size=1000):
        """
        data 每行格式: [set字段值..., where字段值...]
        """
        if not data:
            return
        sql = MsUtil.update_sql(table, set_fields, where_fields)
        update_total = 0
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            db.execute(sql, batch)
            update_total += len(batch)
            Log.log(f">>>>>> {table} 已更新{update_total}")

    @staticmethod
    def update_dict(db: BaseMS, table: str, data: list[dict[str, any]], set_fields: list[str], where_fields: list[str], batch_size=1000):
        """
        data 每行为完整字段的 dict，where_fields 指定作为 WHERE 条件的字段
        set_fields 指定要更新的字段，默认为 dict 中除 where_fields 以外的所有字段
        """
        if not data:
            return
        if not set_fields:
            raise ValueError("没有可更新的字段（所有字段都是 WHERE 条件）")
        rows = [[d[f] for f in set_fields] + [d[f] for f in where_fields] for d in data]
        MsUtil.update(db, table, set_fields, where_fields, rows, batch_size)

    # 获取建表语句
    @staticmethod
    def get_create_table_sql(db:BaseMS, table: str) -> str:
        sql = f"SHOW CREATE TABLE {table}"
        return  db.queryRow(sql)[1] 

    @staticmethod
    def get_primary_key_fields(db:BaseMS, db_name:str, table: str) -> str:
        sql = f"""
            SELECT
                COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = '{db_name}'
            AND TABLE_NAME = '{table}'
            AND CONSTRAINT_NAME = 'PRIMARY'
            ORDER BY ORDINAL_POSITION;
        """
        return db.queryScalar(sql)
    # 获取两个表的交集字段
    @staticmethod
    def get_common_fields(db1:BaseMS, db_name1: str, table1: str, db2:BaseMS, db_name2: str, table2: str):
        """
        返回两个表中都存在的字段列表
        """
        sql1 = f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{db_name1}' AND TABLE_NAME = '{table1}'
            ORDER BY ORDINAL_POSITION
        """
        fields1 = db1.queryColumn(sql1)  # 假设返回 list，例如 ['id','name','age']

        sql2 = f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{db_name2}' AND TABLE_NAME = '{table2}'
            ORDER BY ORDINAL_POSITION
        """
        fields2 = db2.queryColumn(sql2)

        # 取交集
        fields = list(set(fields1) & set(fields2))
        if not fields or len(fields) == 0:
            raise ValueError("没有找到两个表的公共字段")
        return fields

    # 同步表数据，同一数据库下
    @staticmethod
    def sync_table(db:BaseMS, old_db_name: str, old_table: str, new_db_name: str, new_table: str):
        fields = MsUtil.get_common_fields(db, old_db_name, old_table, db,new_db_name, new_table)
        field_str = ", ".join([f"`{f}`" for f in fields])
        sql = f"""
            INSERT INTO {new_db_name}.{new_table} ({field_str})
            SELECT {field_str}
            FROM {old_db_name}.{old_table}
        """
        db.execute(sql)

    @staticmethod
    def exit_table(db:BaseMS, db_name:str, table: str):
        sql = f"""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = '{db_name}'
            AND table_name = '{table}';
        """
        return db.queryScalar(sql)


