import sqlite3
import json
import datetime

# --- 数据库初始化 (您的修改已保留) ---
def init_db():
    """连接数据库并创建任务表（如果不存在的话）"""
    with sqlite3.connect('tasky.db') as conn:
        cursor = conn.cursor()
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            duration_minutes INTEGER,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            details TEXT,
            location TEXT,
            parent_task_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_sql)
    print("数据库'tasky.db'已初始化，任务表'tasks'已准备就绪。")

# --- 技能一：修改此函数，让它返回新任务的ID ---
def add_task_from_dify(dify_json_output):
    """
    接收Dify返回的JSON对象，存入数据库，并返回新任务的ID。
    """
    try:
        with sqlite3.connect('tasky.db') as conn:
            cursor = conn.cursor()
            
            task_details_obj = dify_json_output.get('task_details', {}) or {}
            details_text = task_details_obj.get('description')
            location_text = task_details_obj.get('location') # 假设Dify输出是嵌套的
            
            # 如果Dify输出是扁平的，就像你的测试数据一样，用下面两行
            # details_text = dify_json_output.get('details')
            # location_text = dify_json_output.get('location')

            insert_sql = """
            INSERT INTO tasks (task_name, start_time, end_time, duration_minutes, priority, details, location)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """
            
            task_data = (
                dify_json_output.get('task_name'),
                dify_json_output.get('start_time'),
                dify_json_output.get('end_time'),
                dify_json_output.get('duration_minutes'),
                dify_json_output.get('priority'),
                details_text,
                location_text
            )
            
            cursor.execute(insert_sql, task_data)
            new_task_id = cursor.lastrowid # 获取刚刚插入行的ID
            
        print(f"成功添加主任务: '{dify_json_output.get('task_name')}' (ID: {new_task_id})")
        return new_task_id # 返回这个ID

    except Exception as e:
        print(f"添加主任务失败: {e}")
        return None

# --- 技能二：新增此函数，用来批量添加子任务 ---
def add_subtasks(parent_id: int, subtask_names: list):
    """为指定的父任务批量添加子任务"""
    if not subtask_names:
        return

    try:
        with sqlite3.connect('tasky.db') as conn:
            cursor = conn.cursor()
            
            insert_sql = """
            INSERT INTO tasks (task_name, priority, status, parent_task_id)
            VALUES (?, ?, ?, ?);
            """
            
            tasks_to_add = []
            for name in subtask_names:
                # 子任务默认优先级为'Medium', 状态为'pending'，并关联父任务ID
                tasks_to_add.append((name, 'Medium', 'pending', parent_id))
            
            # executemany可以一次性插入多条数据，效率更高
            cursor.executemany(insert_sql, tasks_to_add)
        
        print(f"[*] 成功为任务ID {parent_id} 添加了 {len(subtask_names)} 个子任务。")
        return True

    except Exception as e:
        print(f"❌ 添加子任务失败: {e}")
        return False

# --- 用于验证的功能：从数据库读取所有任务 (无需修改) ---
def get_all_tasks():
    """查询并打印数据库中的所有任务"""
    with sqlite3.connect('tasky.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks ORDER BY parent_task_id, id;") # 优化排序
        tasks = cursor.fetchall()
    
    print("\n--- Tasky 数据库中的所有任务 ---")
    if not tasks:
        print("数据库中还没有任务。")
    for task in tasks:
        print(dict(task))
    print("---------------------------------")

# 在 database_manager.py 文件末尾添加以下内容

# --- 技能一：学会区分“固定事件” ---
def get_fixed_events(target_date: str):
    """
    查询指定日期的、时间已经固定的事件。
    :param target_date: 日期字符串 "YYYY-MM-DD"
    """
    with sqlite3.connect('tasky.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # SQL查询：选择所有start_time不为空，且日期匹配的行
        query_sql = "SELECT task_name, start_time, end_time FROM tasks WHERE start_time IS NOT NULL AND DATE(start_time) = ?;"
        cursor.execute(query_sql, (target_date,))
        events = cursor.fetchall()
        
        # 将查询结果转换为字典列表
        return [dict(row) for row in events]

# --- 技能二：学会区分“灵活任务” ---
def get_flexible_tasks():
    """查询所有时间未安排的灵活任务"""
    with sqlite3.connect('tasky.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # SQL查询：选择所有start_time为空的行
        query_sql = "SELECT id, task_name, duration_minutes, priority FROM tasks WHERE start_time IS NULL;"
        cursor.execute(query_sql)
        tasks = cursor.fetchall()
        
        return [dict(row) for row in tasks]

# --- 技能三：学会“更新”日程 ---
def update_task_schedule(task_id: int, start_time: str, end_time: str):
    """根据排程结果，更新一个任务的开始和结束时间"""
    try:
        with sqlite3.connect('tasky.db') as conn:
            cursor = conn.cursor()
            update_sql = "UPDATE tasks SET start_time = ?, end_time = ? WHERE id = ?;"
            cursor.execute(update_sql, (start_time, end_time, task_id))
        return True
    except Exception as e:
        print(f"❌ 更新任务ID {task_id} 的日程失败: {e}")
        return False

# --- 更新模拟运行，测试父子任务功能 ---
if __name__ == "__main__":
    # 1. 初始化数据库和表
    init_db()
    
    # 2. 模拟一个需要被分解的主任务
    parent_task_data = {
      "task_name": "策划并举办公司年度技术分享会",
      "start_time": "2025-10-10T09:00:00",
      "duration_minutes": 10080, # 持续一周
      "priority": "High",
      "details": "需要覆盖前端、后端、AI三个领域",
      "location": "公司总部大报告厅"
    }
    
    # 3. 添加主任务，并获取它的ID
    parent_id = add_task_from_dify(parent_task_data)
    
    if parent_id:
        # 4. 模拟LLM分解后得到的子任务列表
        sub_tasks_list_from_llm = [
            "确定分享会主题和议程",
            "邀请内部和外部讲师",
            "设计并发布活动宣传材料",
            "预订场地并安排设备",
            "活动当天现场签到和协调",
            "收集活动反馈并进行总结"
        ]
        
        # 5. 调用新函数，将子任务存入数据库
        add_subtasks(parent_id, sub_tasks_list_from_llm)
    
    # 6. 查询数据库，验证主任务和子任务是否都已成功存入
    get_all_tasks()