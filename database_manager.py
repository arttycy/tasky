# database_manager.py (最终修正版 - 使用绝对路径)

import sqlite3
import json
import datetime
import os # 导入os模块

# --- 新增：定义数据库文件的绝对路径 ---
# __file__ 是一个特殊变量，代表当前这个.py文件的路径
# os.path.abspath(__file__) 获取这个文件的绝对路径
# os.path.dirname(...) 获取这个文件所在的文件夹路径
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# os.path.join(...) 安全地将文件夹路径和文件名拼接起来
DB_PATH = os.path.join(_CURRENT_DIR, 'tasky.db')
print(f"[*] 数据库文件将被定位在: {DB_PATH}") # 增加一个打印，方便调试
# ------------------------------------

def init_db():
    """连接数据库并创建任务表（如果不存在的话）"""
    # 修改：使用绝对路径DB_PATH
    with sqlite3.connect(DB_PATH) as conn:
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
    print("数据库已初始化，任务表'tasks'已准备就绪。")

def add_task_from_dify(dify_json_output):
    """接收Dify返回的JSON对象，存入数据库，并返回新任务的ID。"""
    try:
        # 修改：使用绝对路径DB_PATH
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # ... (这部分逻辑保持不变) ...
            details_text = dify_json_output.get('details')
            location_text = dify_json_output.get('location')

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
            new_task_id = cursor.lastrowid
        
        print(f"成功添加主任务: '{dify_json_output.get('task_name')}' (ID: {new_task_id})")
        return new_task_id
    except Exception as e:
        print(f"添加主任务失败: {e}")
        return None

# --- 所有其他函数也都需要修改连接字符串 ---
def add_subtasks(parent_id: int, subtasks_list: list):
    if not subtasks_list: return
    try:
        # 修改：使用绝对路径DB_PATH
        with sqlite3.connect(DB_PATH) as conn:
            # ... (函数内部其他代码保持不变) ...
            cursor = conn.cursor()
            insert_sql = "INSERT INTO tasks (task_name, duration_minutes, priority, status, parent_task_id) VALUES (?, ?, ?, ?, ?);"
            tasks_to_add = []
            for subtask in subtasks_list:
                tasks_to_add.append((subtask.get('task_name'), subtask.get('duration_minutes'), subtask.get('priority', 'Medium'), 'pending', parent_id))
            cursor.executemany(insert_sql, tasks_to_add)
        print(f"[*] 成功为任务ID {parent_id} 添加了 {len(subtasks_list)} 个子任务。")
        return True
    except Exception as e:
        print(f"❌ 添加子任务失败: {e}")
        return False

def get_all_tasks():
    try:
        # 修改：使用绝对路径DB_PATH
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY parent_task_id, id;")
            tasks = cursor.fetchall()
            return [dict(row) for row in tasks]
    except Exception as e:
        print(f"❌ 查询所有任务失败: {e}")
        return []

def update_task_status(task_id: int, status: str):
    try:
        # 修改：使用绝对路径DB_PATH
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            update_sql = "UPDATE tasks SET status = ? WHERE id = ?;"
            cursor.execute(update_sql, (status, task_id))
        return True
    except Exception as e:
        print(f"❌ 更新任务ID {task_id} 的状态失败: {e}")
        return False

# ... 你可能有的其他函数也需要同样修改 ...