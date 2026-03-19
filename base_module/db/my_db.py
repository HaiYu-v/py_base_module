import pymysql as MySQLdb
import traceback
'''
数据库操作的公共函数

@author: xu.zhengtao
@created: 2024/11/20
@modified: 2024/11/20
'''

class BaseMS():
    def __init__(self, config):
        self.config = config
        self.in_transaction = False  # 标记是否在事务中
        self.connect()
        
    def connect(self):
        self.conn = MySQLdb.connect(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['user'],
            passwd=self.config['passwd'],
            db=self.config['db'],
            charset=self.config['charset']
        )
        self.conn.autocommit(False)  # 关闭自动提交

    def begin_transaction(self):
        """开始事务"""
        if not self.in_transaction:
            self.conn.begin()
            self.in_transaction = True

    def commit_transaction(self):
        """提交事务"""
        if self.in_transaction:
            self.conn.commit()
            self.in_transaction = False

    def rollback_transaction(self):
        """回滚事务"""
        if self.in_transaction:
            self.conn.rollback()
            self.in_transaction = False

    def execute(self, sql, data=[], *, bind_data=[]):
        cursor = self.conn.cursor()
        try:
            if data:
                cursor.executemany(sql,data)
            else:
                cursor.execute(sql,bind_data) 
            if not self.in_transaction:  # 如果不在事务中，自动提交
                self.conn.commit()
        except Exception as e:
            if self.in_transaction:
                self.conn.rollback()
                self.in_transaction = False
            traceback.print_exc()
            raise e
        finally:
            cursor.close()

    def queryAll(self, sql,*,bind_data=[]):
        self.conn.commit()  # 提交任何未完成的事务
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql,bind_data)
            result = cursor.fetchall()

            result = list(result)
            for i in range(len(result)):
                result[i] = list(result[i])

            return result
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            cursor.close()

    def queryAll_dict(self, sql,*,bind_data=[]):
        self.conn.commit()  # 提交任何未完成的事务
        cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)  # 使用 DictCursor
        try:
            cursor.execute(sql,bind_data)
            result = cursor.fetchall()
            return list(result)  # 返回字典列表
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            cursor.close() 

    def queryColumn(self, sql,*,bind_data=[]):
        self.conn.commit()  # 提交任何未完成的事务
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql,bind_data)
            result = cursor.fetchall()
            result_final = []
            for i in range(len(result)):
                result_final.append(str(result[i][0]))
            return result_final
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            cursor.close()

    def queryRow(self,sql,*,bind_data=[]):
        self.conn.commit()  # 提交任何未完成的事务
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql,bind_data)
            result = cursor.fetchone()
            return result if(result) else False
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            cursor.close()

    def queryScalar(self,sql,*,bind_data=[]):
        self.conn.commit()  # 提交任何未完成的事务
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql,bind_data)
            result = cursor.fetchone()
            return result[0] if(result) else False
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            cursor.close()

    def escape_string(self, str):
        return self.conn.escape_string(str)
