# database_manager.py (V1.5 - 新增 update_task_details)

import sqlite3
import json
import datetime
import os

# --- 定义数据库文件的绝对路径 ---
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_CURRENT_DIR, 'tasky.db')

def init_db():
    """连接数据库并创建任务表（如果不存在的话）"""
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
    print("数据库'tasky.db'已初始化，任务表'tasks'已准备就绪。")

def add_task_from_dify(dify_json_output):
    """接收Dify返回的JSON对象，存入数据库，并返回新任务的ID。"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # --- 优化：正确处理嵌套的task_details对象 ---
            task_details_obj = dify_json_output.get('task_details', {}) or {}
            details_text = task_details_obj.get('description')
            location_text = task_details_obj.get('location')

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

def add_subtasks(parent_id: int, subtasks_list: list):
    if not subtasks_list: return True
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            tasks_to_add = []
            for subtask in subtasks_list:
                tasks_to_add.append((
                    subtask.get('task_name'), subtask.get('duration_minutes'),
                    subtask.get('priority', 'Medium'), 'pending', parent_id
                ))
            insert_sql = "INSERT INTO tasks (task_name, duration_minutes, priority, status, parent_task_id) VALUES (?, ?, ?, ?, ?);"
            cursor.executemany(insert_sql, tasks_to_add)
        print(f"[*] 成功为任务ID {parent_id} 添加了 {len(subtasks_list)} 个子任务。")
        return True
    except Exception as e:
        print(f"❌ 添加子任务失败: {e}")
        return False

def get_all_tasks():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks;")
            tasks = cursor.fetchall()
            return [dict(row) for row in tasks]
    except Exception as e:
        print(f"❌ 查询所有任务失败: {e}")
        return []

def update_task_status(task_id: int, status: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            update_sql = "UPDATE tasks SET status = ? WHERE id = ?;"
            cursor.execute(update_sql, (status, task_id))
        return True
    except Exception as e:
        print(f"❌ 更新任务ID {task_id} 的状态失败: {e}")
        return False

def update_task_name(task_id: int, new_name: str):
    """单独更新指定任务的名称"""
    if not new_name or not new_name.strip():
        print(f"❌ 更新失败：任务名称不能为空。")
        return False
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            update_sql = "UPDATE tasks SET task_name = ? WHERE id = ?;"
            cursor.execute(update_sql, (new_name.strip(), task_id))
        print(f"[*] 成功更新任务ID {task_id} 的名称。")
        return True
    except Exception as e:
        print(f"❌ 更新任务ID {task_id} 的名称失败: {e}")
        return False

# --- 新增：专门用于更新任务详情的函数，以解决AttributeError ---
def update_task_details(task_id: int, new_details: str):
    """单独更新指定任务的详情"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            update_sql = "UPDATE tasks SET details = ? WHERE id = ?;"
            cursor.execute(update_sql, (new_details, task_id))
        print(f"[*] 成功更新任务ID {task_id} 的详情。")
        return True
    except Exception as e:
        print(f"❌ 更新任务ID {task_id} 的详情失败: {e}")
        return False

def update_task_content(task_id: int, new_name: str, new_details: str, new_priority: str):
    """更新指定任务的名称、详情和优先级"""
    if not new_name or not new_name.strip():
        print(f"❌ 更新失败：任务名称不能为空。")
        return False
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            update_sql = "UPDATE tasks SET task_name = ?, details = ?, priority = ? WHERE id = ?;"
            cursor.execute(update_sql, (new_name.strip(), new_details, new_priority, task_id))
        print(f"[*] 成功更新任务ID {task_id} 的内容。")
        return True
    except Exception as e:
        print(f"❌ 更新任务ID {task_id} 的内容失败: {e}")
        return False

def delete_task(task_id: int):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            delete_sql = "DELETE FROM tasks WHERE id = ? OR parent_task_id = ?;"
            cursor.execute(delete_sql, (task_id, task_id))
        return True
    except Exception as e:
        print(f"❌ 删除任务ID {task_id} 失败: {e}")
        return False

def get_fixed_events(target_date: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query_sql = "SELECT task_name, start_time, end_time FROM tasks WHERE start_time IS NOT NULL AND DATE(start_time) = ?;"
        cursor.execute(query_sql, (target_date,))
        events = cursor.fetchall()
        return [dict(row) for row in events]

def get_flexible_tasks():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query_sql = "SELECT id, task_name, duration_minutes, priority FROM tasks WHERE start_time IS NULL AND parent_task_id IS NULL;"
        cursor.execute(query_sql)
        tasks = cursor.fetchall()
        return [dict(row) for row in tasks]

def update_task_schedule(task_id: int, start_time: str, end_time: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            update_sql = "UPDATE tasks SET start_time = ?, end_time = ? WHERE id = ?;"
            cursor.execute(update_sql, (start_time, end_time, task_id))
        return True
    except Exception as e:
        print(f"❌ 更新任务ID {task_id} 的日程失败: {e}")
        return False

def postpone_task(task_id: int):
    """将任务顺延，通过清空其开始和结束时间使其变为灵活任务。"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            update_sql = "UPDATE tasks SET start_time = NULL, end_time = NULL WHERE id = ?;"
            cursor.execute(update_sql, (task_id,))
        print(f"[*] 成功顺延任务ID {task_id}。")
        return True
    except Exception as e:
        print(f"❌ 顺延任务ID {task_id} 失败: {e}")
        return False

