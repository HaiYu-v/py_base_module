#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import os
import threading
import subprocess
import sys

'''
日志打印公共函数

@author: xu.zhengtao
@created: 2024/11/20
@modified: 2024/11/20
'''
class Log():
    # 可以通过设置这个变量来控制是否输出日志
    ENABLE_LOG = True
    
    @staticmethod
    def log(msg):
        # 检查是否启用日志输出
        if not Log.ENABLE_LOG:
            return
            
        # 也可以通过环境变量控制
        if os.getenv('DISABLE_LOG', '').lower() in ['true', '1', 'yes']:
            return
            
        time = datetime.datetime.now()
        formatted_time = time.strftime('%Y-%m-%d %H:%M:%S')
        process_id = os.getpid()
        thread_id = threading.get_ident()
        print(f"[PID:{Log.pad_left_underscore(process_id)} - TID:{Log.pad_left_underscore(thread_id)}] [{formatted_time}] {msg}")
    
    # 左补齐下划线,补到长度为5
    @staticmethod
    def pad_left_underscore(s, length: int = 5) -> str:
        s = str(s)
        return s.rjust(length, '0')

    @staticmethod
    def ensure_single_instance():
        """
        检测是否已有相同脚本（相同参数）运行，如果有则退出
        """
        current_script = os.path.abspath(sys.argv[0])
        script_name = os.path.basename(current_script)
        current_pid = os.getpid()
        current_args = " ".join(sys.argv[1:])
        Log.log(f"当前进程: {current_script} [ PID: {current_pid} ] ，参数: {current_args}")

        try:
            # 查找所有运行中的相同脚本（排除当前进程和grep进程）
            cmd = f"ps aux | grep -F '{script_name}' | grep -v 'grep' | grep -v '{current_pid}'"
            result = subprocess.check_output(cmd, shell=True, text=True)
            
            # 检查每个匹配的进程是否参数一致
            for line in result.splitlines():
                parts = line.split()
                if len(parts) < 11:
                    continue
                other_cmd = " ".join(parts[10:])
                # 跳过 conda run 进程
                if "conda run" in other_cmd:
                    continue
                other_args = other_cmd.split(script_name, 1)[-1].strip()
                if other_args == current_args:
                    pid = parts[1]
                    Log.log(f"另一个实例已经在运行 [ PID: {pid} ] ，退出...")
                    sys.exit(1)

        except subprocess.CalledProcessError:
            # 没有找到匹配的进程，继续运行
            pass