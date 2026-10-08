## 项目结构
```
base_module/
├── __init__.py                                           # 模块初始化文件，导出核心类
├── config.py                                             # YAML配置文件加载工具
│
├── 📁 exception/ (异常处理模块)
│   ├── __init__.py                                       # 异常模块初始化
│   └── Business_exception.py                             # 业务异常类（统一错误码、异常链追踪、堆栈继承）
│
├── 📁 info/ (日志与追踪模块)
│   ├── __init__.py                                       # 信息模块初始化
│   ├── log.py                                            # 日志打印工具（进程/线程ID、单实例检测）
│   │
│   └── 📁 tracer/ (链路追踪)
│       └── tracer.py                                     # 无侵入式链路追踪装饰器（@trace、异步支持、树状日志输出）
│
├── 📁 node/ (节点基类)
│   └── base_node.py                                      # 节点/图公共基类（name / name_cn / desc；__call__ 自动挂节点日志）
│
├── 📁 result/ (统一返回体模块)
│   ├── __init__.py                                       # 返回体模块初始化
│   ├── result_enum.py                                    # 返回结果枚举（错误码+消息定义）
│   └── result.py                                         # 统一返回体（泛型支持、success/error/from_enum静态方法）
│
├── 📁 send/ (消息发送模块)
│   ├── __init__.py                                       # 发送模块初始化
│   ├── Isend.py                                          # 发送接口抽象类
│   ├── qi_wei_send.py                                    # 企业微信机器人发送（Markdown、文件、图片、@提醒）
│   └── file_enum.py                                      # 文件类型枚举（扩展名+MIME映射）
│
└── 📁 utils/ (工具类集合)
    ├── __init__.py                                       # 工具模块初始化
    ├── Bean_util.py                                      # Bean工具类（预留）
    ├── byte_util.py                                      # 字节工具类
    ├── Country_util.py                                   # 国家工具类
    ├── field_util.py                                     # 字段工具（类型转换、列表截取拼接）
    ├── json_util.py                                      # JSON工具类
    ├── math_util.py                                      # 数学工具（比值、统计值、千分位、百分比整数化、总和平衡）
    ├── time_util.py                                      # 时间工具（格式转换、日/月/年初末、上月、前N天）
    │
    └── 📁 file/ (文件操作)
        ├── file_util.py                                  # 文件工具类
        └── table_util.py                                 # 表格工具类

📦 项目配置
├── pyproject.toml                                        # Python项目配置文件（依赖 + dev 依赖组）
├── uv.lock                                               # 依赖锁定文件（uv sync 生成，需提交）
└── README.md                                             # 项目说明文档
```
