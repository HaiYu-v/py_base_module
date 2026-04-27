
from dataclasses import dataclass, fields
import uuid
from base_module import BaseCK
from base_module import SqlUtil
from base_module.info.log import Log

@dataclass(frozen=True)
class ReplaceConst:
    REPLACE_TABLE: str
    def __str__(self):
        return self.REPLACE_TABLE


class ReplaceTableContext:
    def __init__(self, db:BaseCK, table:str, replace_name:str):
        self.db: BaseCK = db
        self.table: str = table
        self.replace_name: str = replace_name
        self.replace_table: ReplaceConst = None

    def __enter__(self) -> ReplaceConst:
        self.replace_table = CkUtil.create_replace_table(self.db, self.table, self.replace_name)
        return self.replace_table  # as 后面的变量

    def __exit__(self, exc_type, exc_val, exc_tb):
        CkUtil.delete_table(self.db, self.replace_table)
        return False  # False = 不吞异常，异常继续向上抛     


class CkUtil:
    # 禁止插入
    FORBID_INSERT = False
    
    @staticmethod
    def insert_sql(table: str, fields: list[str]) -> str:
        """
        生成 ClickHouse 插入 SQL
        注意：ClickHouse 通常用 client.execute(sql, data_list)
        :param table: 表名
        :param fields: 列名列表
        :return: INSERT SQL
        """
        cols = ", ".join(f"`{c}`" for c in fields)
        sql = f"INSERT INTO {table} ({cols}) VALUES "
        return sql

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
    def insert(db:BaseCK, table: str, fields: list[str], data: list[list]):
        CkUtil.check(fields,data)
        sql = CkUtil.insert_sql(table, fields)
        if not CkUtil.FORBID_INSERT:
            db.execute(sql, data)

    @staticmethod
    def insert_dict(db:BaseCK, table: str,data: list[dict[str, any]]):
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
        CkUtil.insert(db, table, fields, insert_data)
    
    # 删除表
    @staticmethod
    def delete_table(db: BaseCK, replace_const: ReplaceConst) -> None:
        return db.execute(f"DROP TABLE IF EXISTS {replace_const.REPLACE_TABLE} SYNC")

    # 获取建表语句
    @staticmethod
    def get_create_table_sql(db:BaseCK, table: str) -> str:
        sql = f"SHOW CREATE TABLE {table}"
        return db.queryScalar(sql)

    # 获取主键字段
    @staticmethod
    def get_primary_key_fields(db:BaseCK, db_name:str, table: str) -> str:
        sql = f"""
            SELECT
                primary_key
            FROM system.tables
            WHERE database = '{db_name}'
            AND name = '{table}';
        """
        return db.queryScalar(sql)

    # 获取两个表的交集字段
    @staticmethod
    def get_common_fields(db1:BaseCK, db_name1:str, table1: str, db2:BaseCK, db_name2:str, table2: str):
        sql = f"""
            SELECT groupArray(name) AS columns
            FROM (
                SELECT name
                FROM system.columns
                WHERE database = '{db_name1}' AND table = '{table1}'
                ORDER BY position
            )
        """
        fields1 = db1.queryScalar(sql)

        sql = f"""
            SELECT groupArray(name) AS columns
            FROM (
                SELECT name
                FROM system.columns
                WHERE database = '{db_name2}' AND table = '{table2}'
                ORDER BY position
            )
        """
        fields2 = db2.queryScalar(sql)
        fields = list(set(fields1) & set(fields2))
        if not fields or len(fields) == 0:
            raise ValueError("没有找到两个表的公共字段")
        return fields

    # 同步表数据, 同一数据库下
    @staticmethod
    def sync_table(db:BaseCK, old_db_name:str, old_table: str,  new_db_name:str, new_table: str):
        fields = CkUtil.get_common_fields(db, old_db_name, old_table, db, new_db_name, new_table)
        field_str = ", ".join(fields)
        sql = f"""
            INSERT INTO {new_db_name}.{new_table} ({field_str})
            SELECT {field_str}
            FROM {old_db_name}.{old_table}
        """
        db.execute(sql)

    @staticmethod
    def exit_table(db:BaseCK, db_name:str, table: str):
        sql = f"EXISTS {db_name}.{table}"
        return db.queryScalar(sql)
        
    @staticmethod
    def create_replace_table(db: BaseCK, table_name: str, replace_name: str = '') -> ReplaceConst:
        if replace_name == '':
            replace_name = f"{table_name}_{uuid.uuid4().hex}"

        db.execute(f"DROP TABLE IF EXISTS {replace_name} SYNC")
        db.execute(f"CREATE TABLE {replace_name} AS {table_name}")

        return ReplaceConst(REPLACE_TABLE=replace_name)

    # 使用with来维护临时表的创建和销毁
    @staticmethod
    def with_replace(db: BaseCK, table_name: str, replace_name: str = '') -> ReplaceConst:
        return ReplaceTableContext(db, table_name,replace_name)

    # 创建某张表的内存临时表
    @staticmethod
    def create_tomporary_table(db: BaseCK, table_name: str) -> str:
        temp_table_name = f"temp_{uuid.uuid4().hex}"
        db.execute(f"CREATE TEMPORARY TABLE {temp_table_name} AS SELECT * FROM {table_name} WHERE 1=0")
        return temp_table_name
    
    # 创建并写入内存临时表(指定fields)
    @staticmethod
    def insert_temporary_table(ck_db:BaseCK, data:list[list], fields:list[tuple[str, str]]) -> str:
        table = f"temporary_{uuid.uuid4().hex}"
        fields_sql = SqlUtil.create_fields(fields)

        sql = f"CREATE TEMPORARY TABLE {table} {fields_sql} ENGINE = TinyLog"
        ck_db.execute(sql)

        fields = [field[0] for field in fields]
        CkUtil.check(fields,data)
        sql = CkUtil.insert_sql(table, fields)
        ck_db.execute(sql, data)
        return table
    
    # 批量进行分区替换
    @staticmethod
    def replace_partitions(ck_db:BaseCK,target_table:str,replace_table:str,partitions:list[list[str]]):
        for partition in partitions:
            sql = f"""
                ALTER TABLE {target_table}
                REPLACE PARTITION ({','.join(partition)})
                FROM {replace_table};    
            """
            if not CkUtil.FORBID_INSERT:
                ck_db.execute(sql)
                Log.log(f">>>>>> [target_table] 分区替换[{','.join(partition)}]")
    