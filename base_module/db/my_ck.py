#!/usr/bin/env python
# -*- coding: utf-8 -*-
import inspect
import re
from base_module.exception.Business_exception import BusinessException
from clickhouse_driver import Client
import traceback
'''
ClickHouse数据库操作的公共函数

@author: assistant
@created: 2024/12/26
@modified: 2024/12/26
'''

class BaseCK():
    def __init__(self, config):
        self.config = config
        self.connect()
        
    def connect(self):
        """连接到ClickHouse数据库"""
        try:
            self.client = Client(
                host=self.config['host'],
                port=self.config.get('port', 9000),  # ClickHouse 默认端口
                user=self.config['user'],
                password=self.config['passwd'],
                database=self.config['db'],
                settings={
                    'use_client_time_zone': True,
                }
            )
        except Exception as e:
            trace = inspect.trace()
            exc = BusinessException(f"连接ClickHouse失败", None, e, trace)
            raise exc 

    def reconnect(self):
        """重新连接"""
        try:
            self.disconnect()
            self.connect()
        except Exception as e:
            trace = inspect.trace()
            exc = BusinessException(f"重连失败", None, e, trace)
            raise exc 

    def execute(self, sql, data=[], *, bind_data=[]):
        """执行SQL语句（INSERT, UPDATE, DELETE等）"""
        try:
            if data:
                # ClickHouse 批量插入
                result = self.client.execute(sql, data)
            elif bind_data:
                result = self.client.execute(sql, bind_data)
            else:
                result = self.client.execute(sql)
            return result
        except Exception as e:
            trace = inspect.trace()
            cleaned_sql = re.sub(r'\s+', ' ', sql).strip()[:2000]
            exc = BusinessException(f"执行sql失败,sql:\n{cleaned_sql}\n", None, e, trace)
            raise exc 

    def queryAll(self, sql, *, bind_data=[]):
        """查询所有记录"""
        try:
            if bind_data:
                result = self.client.execute(sql, bind_data)
            else:
                result = self.client.execute(sql)
            
            # 转换为列表格式，保持与MySQL版本一致
            result = list(result)
            for i in range(len(result)):
                result[i] = list(result[i])
            
            return result
        except Exception as e:
            trace = inspect.trace()
            cleaned_sql = re.sub(r'\s+', ' ', sql).strip()[:2000]
            exc = BusinessException(f"查询所有记录失败,sql:\n{cleaned_sql}\n", None, e, trace)
            raise exc 

    def queryAll_dict(self, sql, *, bind_data=[]):
        """查询所有记录，返回字典列表"""
        try:
            if bind_data:
                result, columns = self.client.execute(sql, bind_data, with_column_types=True)
            else:
                result, columns = self.client.execute(sql, with_column_types=True)
            
            # 提取列名
            column_names = [col[0] for col in columns]
            
            # 转换为字典列表
            dict_result = []
            for row in result:
                dict_result.append(dict(zip(column_names, row)))
            return dict_result
        except Exception as e:
            trace = inspect.trace()
            cleaned_sql = re.sub(r'\s+', ' ', sql).strip()[:2000]
            exc = BusinessException(f"查询所有记录(字典)失败,sql:\n{cleaned_sql}\n", None, e, trace)
            raise exc 

    def queryColumn(self, sql, *, bind_data=[]):
        """查询单列数据"""
        try:
            if bind_data:
                result = self.client.execute(sql, bind_data)
            else:
                result = self.client.execute(sql)
            
            result_final = []
            for row in result:
                result_final.append(str(row[0]))
            return result_final
        except Exception as e:
            trace = inspect.trace()
            cleaned_sql = re.sub(r'\s+', ' ', sql).strip()[:2000]
            exc = BusinessException(f"查询单列失败,sql:\n{cleaned_sql}\n", None, e, trace)
            raise exc 

    def queryRow(self, sql, *, bind_data=[]):
        """查询单行数据"""
        try:
            if bind_data:
                result = self.client.execute(sql, bind_data)
            else:
                result = self.client.execute(sql)
            
            return result[0] if result else False
        except Exception as e:
            trace = inspect.trace()
            cleaned_sql = re.sub(r'\s+', ' ', sql).strip()[:2000]
            exc = BusinessException(f"查询单行失败,sql:\n{cleaned_sql}\n", None, e, trace)
            raise exc 

    def queryScalar(self, sql, *, bind_data=[]):
        """查询单个值"""
        try:
            if bind_data:
                result = self.client.execute(sql, bind_data)
            else:
                result = self.client.execute(sql)
            
            return result[0][0] if result else False
        except Exception as e:
            trace = inspect.trace()
            cleaned_sql = re.sub(r'\s+', ' ', sql).strip()[:2000]
            exc = BusinessException(f"查询单个值失败,sql:\n{cleaned_sql}\n", None, e, trace)
            raise exc 

    def insert_dataframe(self, table_name, df):
        """
        将pandas DataFrame插入到ClickHouse表中
        
        Args:
            table_name (str): 表名
            df (pandas.DataFrame): 要插入的数据
        """
        try:
            self.client.insert_dataframe(f"INSERT INTO {table_name} VALUES", df)
            return True
        except Exception as e:
            trace = inspect.trace()
            exc = BusinessException('插入DataFrame失败', None, e, trace)
            raise exc 

    def execute_with_progress(self, sql, bind_data=[], progress_callback=None):
        """
        执行SQL并提供进度回调（适用于大数据量查询）
        
        Args:
            sql (str): SQL语句
            bind_data (list): 绑定参数
            progress_callback (function): 进度回调函数
        """
        try:
            settings = {}
            if progress_callback:
                settings['send_progress_in_http_headers'] = 1
            
            result = self.client.execute(
                sql, 
                bind_data,
                settings=settings,
                with_column_types=True
            )
            return result
        except Exception as e:
            trace = inspect.trace()
            exc = BusinessException('执行SQL并提供进度回调失败', None, e, trace)
            raise exc 

    def get_table_info(self, table_name):
        """获取表结构信息"""
        try:
            sql = f"DESCRIBE TABLE {table_name}"
            result = self.client.execute(sql)
            return list(result)
        except Exception as e:
            trace = inspect.trace()
            exc = BusinessException('获取表结构信息失败', None, e, trace)
            raise exc 

    def get_database_tables(self):
        """获取当前数据库的所有表名"""
        try:
            sql = "SHOW TABLES"
            result = self.client.execute(sql)
            return [row[0] for row in result]
        except Exception as e:
            trace = inspect.trace()
            exc = BusinessException('获取当前数据库的所有表名失败', None, e, trace)
            raise exc 

    def disconnect(self):
        """断开连接"""
        try:
            if hasattr(self, 'client') and self.client:
                self.client.disconnect()
        except Exception as e:
            trace = inspect.trace()
            exc = BusinessException('断开连接失败', None, e, trace)
            raise exc 

    def __del__(self):
        """析构函数，确保连接被正确关闭"""
        self.disconnect()

    def get_config(self):
        return self.config
    def get_host(self):
        return self.config['host']
    def get_port(self):
        return self.config['port']
    def get_user(self):
        return self.config['user']
    def get_passwd(self):
        return self.config['passwd']
    def get_db(self):
        return self.config['db']