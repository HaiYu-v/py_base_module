#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pymysql as MySQLdb
from queue import Queue, Empty
import threading
import traceback


'''
MySQL 数据库的连接池

@author: assistant
@created: 2025/11/06
'''

class BaseMsPool:
    """MySQL 连接池"""
    
    def __init__(self, config, pool_size=5, max_overflow=10):
        """
        Args:
            dbname: 数据库配置名称
            pool_size: 核心池大小
            max_overflow: 最大溢出连接数（超出核心池时可创建的额外连接数）
        """
        self.config = config
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        
        # 连接池（空闲连接）
        self._pool = Queue(maxsize=pool_size + max_overflow)
        # 当前连接数
        self._current_size = 0
        self._lock = threading.Lock()
        
        # 初始化核心连接
        for _ in range(pool_size):
            conn = self._create_connection()
            self._pool.put(conn)
            self._current_size += 1
    
    def _create_connection(self):
        """创建新连接"""
        try:
            
            conn = MySQLdb.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                passwd=self.config['passwd'],
                db=self.config['db'],
                charset=self.config['charset'],
                connect_timeout=10,  # 连接超时 10秒
                read_timeout=300,    # 读取超时 5分钟
                write_timeout=300    # 写入超时 5分钟
            )
            conn.autocommit(False)  # 关闭自动提交
            return conn
        except Exception as e:
            print(f"创建连接失败: {e}")
            traceback.print_exc()
            raise
    
    def get_connection(self, timeout=30):
        """
        从池中获取连接（带健康检查）
        
        Args:
            timeout: 获取超时时间（秒）
        
        Returns:
            MySQLdb Connection 对象
        """
        try:
            # 尝试从池中获取空闲连接
            conn = self._pool.get(timeout=timeout)
            
            # 健康检查：使用 ping() 方法验证连接是否有效
            try:
                conn.ping(reconnect=False)
                return conn
            except Exception as e:
                # 连接失效，关闭并重新创建
                print(f"[连接池] 连接失效，重新创建连接: {e}")
                try:
                    conn.close()
                except:
                    pass
                # 创建新连接替换失效的连接
                conn = self._create_connection()
                return conn
                
        except Empty:
            # 池中无空闲连接，检查是否可以创建新连接
            with self._lock:
                if self._current_size < (self.pool_size + self.max_overflow):
                    conn = self._create_connection()
                    self._current_size += 1
                    return conn
                else:
                    raise Exception("连接池已满，无法获取连接")
    
    def release_connection(self, conn):
        """归还连接到池中"""
        try:
            # 确保连接不在事务中
            try:
                conn.rollback()  # 回滚任何未提交的事务
            except:
                pass
            self._pool.put(conn, block=False)
        except:
            # 池已满，关闭连接
            try:
                conn.close()
            except:
                pass
            with self._lock:
                self._current_size -= 1
    
    def execute(self, sql, data=[], *, bind_data=[]):
        """执行SQL（自动获取和释放连接）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if data:
                cursor.executemany(sql, data)
            else:
                cursor.execute(sql, bind_data)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"执行SQL失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def queryAll(self, sql, *, bind_data=[]):
        """查询所有记录（自动获取和释放连接）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, bind_data)
            result = cursor.fetchall()
            
            result = list(result)
            for i in range(len(result)):
                result[i] = list(result[i])
            
            return result
        except Exception as e:
            print(f"查询所有记录失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def queryColumn(self, sql, *, bind_data=[]):
        """查询单列数据（自动获取和释放连接）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, bind_data)
            result = cursor.fetchall()
            result_final = []
            for i in range(len(result)):
                result_final.append(str(result[i][0]))
            return result_final
        except Exception as e:
            print(f"查询单列失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def queryRow(self, sql, *, bind_data=[]):
        """查询单行数据（自动获取和释放连接）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, bind_data)
            result = cursor.fetchone()
            return result if result else False
        except Exception as e:
            print(f"查询单行失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def queryScalar(self, sql, *, bind_data=[]):
        """查询单个值（自动获取和释放连接）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, bind_data)
            result = cursor.fetchone()
            return result[0] if result else False
        except Exception as e:
            print(f"查询单个值失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def get_session(self):
        """
        获取一个会话连接（用于事务等需要保持连接的场景）
        返回一个上下文管理器
        
        用法:
            with pool.get_session() as session:
                session.begin_transaction()
                session.execute("INSERT INTO ...")
                session.execute("UPDATE ...")
                session.commit_transaction()
        """
        return _PoolSession(self)
    
    def disconnect(self):
        """断开连接（关闭连接池）"""
        self.close_all()
    
    def close_all(self):
        """关闭所有连接"""
        while not self._pool.empty():
            try:
                conn = self._pool.get(block=False)
                conn.close()
            except:
                pass
        self._current_size = 0


class _PoolSession:
    """连接池会话 - 保持单个连接用于事务等场景"""
    
    def __init__(self, pool):
        self.pool = pool
        self.conn = None
        self.in_transaction = False
    
    def __enter__(self):
        """进入上下文，获取连接"""
        self.conn = self.pool.get_connection()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，释放连接"""
        # 如果还在事务中且发生异常，自动回滚
        if self.in_transaction and exc_type is not None:
            try:
                self.rollback_transaction()
            except:
                pass
        
        if self.conn:
            self.pool.release_connection(self.conn)
        return False
    
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
        """在当前会话连接上执行 SQL"""
        cursor = self.conn.cursor()
        try:
            if data:
                cursor.executemany(sql, data)
            else:
                cursor.execute(sql, bind_data)
            if not self.in_transaction:  # 如果不在事务中，自动提交
                self.conn.commit()
        except Exception as e:
            if self.in_transaction:
                self.conn.rollback()
                self.in_transaction = False
            print(f"执行SQL失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            cursor.close()
    
    def queryAll(self, sql, *, bind_data=[]):
        """在当前会话连接上查询所有记录"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql, bind_data)
            result = cursor.fetchall()
            
            result = list(result)
            for i in range(len(result)):
                result[i] = list(result[i])
            
            return result
        except Exception as e:
            print(f"查询所有记录失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            cursor.close()
    
    def queryColumn(self, sql, *, bind_data=[]):
        """在当前会话连接上查询单列"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql, bind_data)
            result = cursor.fetchall()
            result_final = []
            for i in range(len(result)):
                result_final.append(str(result[i][0]))
            return result_final
        except Exception as e:
            print(f"查询单列失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            cursor.close()
    
    def queryRow(self, sql, *, bind_data=[]):
        """在当前会话连接上查询单行"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql, bind_data)
            result = cursor.fetchone()
            return result if result else False
        except Exception as e:
            print(f"查询单行失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            cursor.close()
    
    def queryScalar(self, sql, *, bind_data=[]):
        """在当前会话连接上查询单个值"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql, bind_data)
            result = cursor.fetchone()
            return result[0] if result else False
        except Exception as e:
            print(f"查询单个值失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            cursor.close()


# 全局连接池实例（单例模式）
_pools = {}
_pools_lock = threading.Lock()

def get_db_pool(dbname, pool_size=4, max_overflow=5):
    """
    获取连接池（单例）
    
    Args:
        dbname: 数据库配置名称
        pool_size: 核心池大小
        max_overflow: 最大溢出连接数
    
    Returns:
        DBConnectionPool 实例
    """
    pool_key = f"{dbname}_{pool_size}_{max_overflow}"
    if pool_key not in _pools:
        with _pools_lock:
            if pool_key not in _pools:  # 双重检查
                _pools[pool_key] = DBConnectionPool(dbname, pool_size, max_overflow)
    return _pools[pool_key]

