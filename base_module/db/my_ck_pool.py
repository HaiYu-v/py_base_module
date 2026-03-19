#!/usr/bin/env python
# -*- coding: utf-8 -*-

from clickhouse_driver import Client
from queue import Queue, Empty
import threading
import traceback

'''
ClickHouse ck的连接池

@author: huyabei
@created: 2025/10/28
'''

class BaseCkPool:
    """ClickHouse 连接池"""
    
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
            client = Client(
                host=self.config['host'],
                port=self.config.get('port', 9000),
                user=self.config['user'],
                password=self.config['passwd'],
                database=self.config['db'],
                settings={
                    'use_client_time_zone': True
                },
                # 连接超时配置
                connect_timeout=10,       # 连接超时 10秒
                send_receive_timeout=300, # 发送接收超时 5分钟
                sync_request_timeout=300, # 同步请求超时 5分钟
            )
            return client
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
            ClickHouse Client 对象
        """
        try:
            # 尝试从池中获取空闲连接
            conn = self._pool.get(timeout=timeout)
            
            # 健康检查：尝试执行简单查询验证连接是否有效
            try:
                conn.execute('SELECT 1')
                return conn
            except Exception as e:
                # 连接失效，关闭并重新创建
                print(f"[连接池] 连接失效，重新创建连接: {e}")
                try:
                    conn.disconnect()
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
            self._pool.put(conn, block=False)
        except:
            # 池已满，关闭连接
            try:
                conn.disconnect()
            except:
                pass
            with self._lock:
                self._current_size -= 1
    
    def execute(self, sql, data=[], *, bind_data=[]):
        """执行SQL（自动获取和释放连接）"""
        conn = self.get_connection()
        try:
            if data:
                result = conn.execute(sql, data)
            elif bind_data:
                result = conn.execute(sql, bind_data)
            else:
                result = conn.execute(sql)
            return result
        except Exception as e:
            print(f"执行SQL失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            self.release_connection(conn)
    
    def queryAll(self, sql, *, bind_data=[]):
        """查询所有记录（自动获取和释放连接）"""
        conn = self.get_connection()
        try:
            if bind_data:
                result = conn.execute(sql, bind_data)
            else:
                result = conn.execute(sql)
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
            self.release_connection(conn)
    
    def queryColumn(self, sql, *, bind_data=[]):
        """查询单列数据（自动获取和释放连接）"""
        conn = self.get_connection()
        try:
            if bind_data:
                result = conn.execute(sql, bind_data)
            else:
                result = conn.execute(sql)
            result_final = []
            for row in result:
                result_final.append(str(row[0]))
            return result_final
        except Exception as e:
            print(f"查询单列失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            self.release_connection(conn)
    
    def queryRow(self, sql, *, bind_data=[]):
        """查询单行数据（自动获取和释放连接）"""
        conn = self.get_connection()
        try:
            if bind_data:
                result = conn.execute(sql, bind_data)
            else:
                result = conn.execute(sql)
            if result:
                return list(result[0])
            return False
        except Exception as e:
            print(f"查询单行失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            self.release_connection(conn)
    
    def queryScalar(self, sql, *, bind_data=[]):
        """查询单个值（自动获取和释放连接）"""
        conn = self.get_connection()
        try:
            if bind_data:
                result = conn.execute(sql, bind_data)
            else:
                result = conn.execute(sql)
            return result[0][0] if result else False
        except Exception as e:
            print(f"查询单个值失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
        finally:
            self.release_connection(conn)
    
    def get_session(self):
        """
        获取一个会话连接（用于临时表等需要保持连接的场景）
        返回一个上下文管理器
        
        用法:
            with pool.get_session() as session:
                session.execute("CREATE TEMPORARY TABLE ...")
                session.execute("INSERT INTO ...")
                result = session.queryAll("SELECT FROM ...")
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
                conn.disconnect()
            except:
                pass
        self._current_size = 0


class _PoolSession:
    """连接池会话 - 保持单个连接用于临时表等场景"""
    
    def __init__(self, pool):
        self.pool = pool
        self.conn = None
    
    def __enter__(self):
        """进入上下文，获取连接"""
        self.conn = self.pool.get_connection()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，释放连接"""
        if self.conn:
            self.pool.release_connection(self.conn)
        return False
    
    def execute(self, sql, data=[], *, bind_data=[]):
        """在当前会话连接上执行 SQL"""
        try:
            if data:
                return self.conn.execute(sql, data)
            elif bind_data:
                return self.conn.execute(sql, bind_data)
            else:
                return self.conn.execute(sql)
        except Exception as e:
            print(f"执行SQL失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
    
    def queryAll(self, sql, *, bind_data=[]):
        """在当前会话连接上查询所有记录"""
        try:
            if bind_data:
                result = self.conn.execute(sql, bind_data)
            else:
                result = self.conn.execute(sql)
            result = list(result)
            for i in range(len(result)):
                result[i] = list(result[i])
            return result
        except Exception as e:
            print(f"查询所有记录失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
    
    def queryColumn(self, sql, *, bind_data=[]):
        """在当前会话连接上查询单列"""
        try:
            if bind_data:
                result = self.conn.execute(sql, bind_data)
            else:
                result = self.conn.execute(sql)
            result_final = []
            for row in result:
                result_final.append(str(row[0]))
            return result_final
        except Exception as e:
            print(f"查询单列失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
    
    def queryRow(self, sql, *, bind_data=[]):
        """在当前会话连接上查询单行"""
        try:
            if bind_data:
                result = self.conn.execute(sql, bind_data)
            else:
                result = self.conn.execute(sql)
            if result:
                return list(result[0])
            return False
        except Exception as e:
            print(f"查询单行失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise
    
    def queryScalar(self, sql, *, bind_data=[]):
        """在当前会话连接上查询单个值"""
        try:
            if bind_data:
                result = self.conn.execute(sql, bind_data)
            else:
                result = self.conn.execute(sql)
            return result[0][0] if result else False
        except Exception as e:
            print(f"查询单个值失败: {e}")
            print(f"SQL: {sql}")
            traceback.print_exc()
            raise


# 全局连接池实例（单例模式）
_pools = {}
_pools_lock = threading.Lock()

def get_ck_pool(dbname, pool_size=4, max_overflow=5):
    """
    获取连接池（单例）
    
    Args:
        dbname: 数据库配置名称
        pool_size: 核心池大小
        max_overflow: 最大溢出连接数
    
    Returns:
        CKConnectionPool 实例
    """
    pool_key = f"{dbname}_{pool_size}_{max_overflow}"
    if pool_key not in _pools:
        with _pools_lock:
            if pool_key not in _pools:  # 双重检查
                _pools[pool_key] = CKConnectionPool(dbname, pool_size, max_overflow)
    return _pools[pool_key]

