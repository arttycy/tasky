# app.py (V2 - 具备完整排程逻辑)

import database_manager
import task_scheduler
import json

def setup_test_data():
    """清空并创建一些用于测试的混合数据"""
    print("[*] 正在准备测试数据...")
    # 为了防止重复添加，先简单地删除旧数据库文件
    import os
    if os.path.exists('tasky.db'):
        os.remove('tasky.db')
        
    database_manager.init_db()
    
    # 1. 添加一个固定的事件（用户已手动设定时间）
    fixed_event = {
        "task_name": "团队关键决策会议",
        "start_time": "2025-09-19T10:00:00",
        "end_time": "2025-09-19T11:30:00",
        "priority": "High",
        "details": "决定Q4最终方向",
        "location": "大会议室"
    }
    database_manager.add_task_from_dify(fixed_event)
    
    # 2. 添加几个灵活的任务（等待AI排程）
    flexible_tasks = [
        {"task_name": "完成项目A的设计文档", "duration_minutes": 180, "priority": "High"},
        {"task_name": "回复本周所有积压邮件", "duration_minutes": 60, "priority": "Medium"},
        {"task_name": "准备下周工作计划PPT", "duration_minutes": 90, "priority": "Medium"},
    ]
    for task in flexible_tasks:
        database_manager.add_task_from_dify(task) # 复用add_task函数，不提供时间即可
    print("[*] 测试数据准备完毕！")


def run_master_schedule_for_date(target_date: str):
    """
    为指定日期运行一次总排程。
    """
    print(f"\n--- 开始为日期 {target_date} 进行智能排程 ---")
    
    # 1. 从数据库获取所需信息
    print("[1] 从数据库获取固定事件和灵活任务...")
    fixed_events = database_manager.get_fixed_events(target_date)
    flexible_tasks = database_manager.get_flexible_tasks()
    
    if not flexible_tasks:
        print("[!] 没有需要排程的灵活任务，流程结束。")
        return

    print(f"[*] 查找到 {len(fixed_events)} 个固定事件。")
    print(f"[*] 查找到 {len(flexible_tasks)} 个灵活任务需要安排。")
    
    # 2. 调用智能排程器AI大脑
    print("[2] 调用 task_scheduler AI大脑进行规划...")
    # 我们需要从灵活任务中提取特定字段给AI
    tasks_for_ai = [
        {"task_name": t["task_name"], "duration_minutes": t["duration_minutes"], "priority": t["priority"]}
        for t in flexible_tasks
    ]
    schedule_result = task_scheduler.schedule_tasks(tasks_for_ai, fixed_events, target_date)
    
    if not schedule_result:
        print("❌ AI排程失败，流程终止。")
        return
        
    print("[*] AI大脑返回了建议的日程表。")
    
    # 3. 将排程结果写回数据库
    print("[3] 正在将新日程更新到数据库...")
    
    # 为了通过任务名找到ID，我们先创建一个映射
    task_name_to_id_map = {t["task_name"]: t["id"] for t in flexible_tasks}
    
    success_count = 0
    for scheduled_item in schedule_result:
        task_name = scheduled_item.get("task_name")
        # 忽略AI可能生成的“短暂休息”等非原始任务
        if task_name in task_name_to_id_map:
            task_id = task_name_to_id_map[task_name]
            start_time = scheduled_item.get("start_time")
            end_time = scheduled_item.get("end_time")
            
            if database_manager.update_task_schedule(task_id, start_time, end_time):
                success_count += 1
                
    print(f"[*] 成功更新了 {success_count} 个任务的日程。")


if __name__ == "__main__":
    # 准备一些初始数据用于测试
    setup_test_data()
    
    # 运行总排程
    run_master_schedule_for_date("2025-09-19")
    
    # 查看最终结果
    print("\n--- 查看排程后的最终数据库状态 ---")
    database_manager.get_all_tasks()