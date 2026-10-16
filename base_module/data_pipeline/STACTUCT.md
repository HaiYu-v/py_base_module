
## 单个处理节点
- 开始时间
- 结束时间
- 状态
- 消息
- 节点id
- 上一节点id

## 基础任务表
- e_id: 对应实体的id
- task_name
- date (YYYY-MM-dd)
- opening (开始时间, 过了这个时间任务才可以执行; 留空 = 随时可执行, 默认为空)
- pre_task_table (前置任务的表名, 如 reading_task; 留空 = 没有前置)
- pre_id (前置任务的id, 在 pre_task_table 那张表里)
- pre_state (前置任务要达到的状态; 前置到了这个状态后, 本条任务才可以执行)
- start_data , json
- end_data, json
- extra_dict, json
- state
- deadline (截至时间, 默认创建时间+24h; 有 opening 时默认为 opening+24h)
- run_id, 运行id

唯一键: e_id, task_name, date
start_data 和 end_data是同一类型的对象

## 处理流程
1. 创建task, 赋予e_id, task_name, 
2. start_data初始化
  - start_data赋值
3. 定时脚本读取start_data, 开始执行 (已到 opening 的才读; opening 为空 = 随时; 配了 pre_id 的还要前置任务到了 pre_state)
4. 执行过程中打印日志
5. 收集日志
6. 最终结果输入到end_data

## 审核和应用
- 比对start_data和end_data
- 审核流水线是否正确, 产出是否正确
- 用end_data 替换掉先有的实体数据
   
