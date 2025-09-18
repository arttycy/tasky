# task_scheduler.py 文件内容

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# --- 智能排程器的Prompt ---
PROMPT_TEMPLATE = """
# 角色
你是一位极其出色的行政助理和时间管理大师。

# 任务
根据我提供的“待办任务列表”和一份“已有日程”，为指定日期制定一份最优的、详细到分钟的时间表。

# 规则与约束
1.  **绝对不能重叠**: 新安排的任务时间不能与`已有日程`中的任何时间重叠。
2.  **尊重任务时长**: 安排给每个任务的时间段必须等于其`duration_minutes`。
3.  **优先级优先**: `priority`为'High'的任务需要被最先安排进日程表。
4.  **工作时间**: 核心工作任务尽量安排在上午9点到12点，下午2点到8点之间。

# 输出格式
严格返回一个只包含`schedule_result`键的JSON对象。其值为一个对象数组，数组中的每个任务都必须有`task_name`, `start_time` (ISO 8601格式), 和 `end_time` (ISO 8601格式) 这三个字段。

# 上下文
需要进行排程的日期: {target_date}
已有日程 (这些是固定不变的，必须避开): 
{existing_events_str}

待办任务列表 (请将这些任务安排到空白时间): 
{tasks_to_schedule_str}
"""

def schedule_tasks(tasks_to_schedule: list, existing_events: list, target_date: str):
    """
    接收任务列表和已有日程，调用LLM进行智能排程。
    
    :param tasks_to_schedule: 包含待办任务字典的列表
    :param existing_events: 包含已有日程字典的列表
    :param target_date: 目标排程日期，格式 "YYYY-MM-DD"
    :return: 包含排程结果的字典列表，或在失败时返回None
    """
    print("[*] 接收到排程请求...")
    
    # a. 将列表数据格式化为更易读的字符串，方便LLM理解
    tasks_to_schedule_str = json.dumps(tasks_to_schedule, indent=2, ensure_ascii=False)
    existing_events_str = json.dumps(existing_events, indent=2, ensure_ascii=False)
    
    # b. 格式化最终的Prompt
    final_prompt = PROMPT_TEMPLATE.format(
        target_date=target_date,
        existing_events_str=existing_events_str,
        tasks_to_schedule_str=tasks_to_schedule_str
    )
    
    # c. 准备API请求
    headers = { 'Authorization': f'Bearer {DEEPSEEK_API_KEY}', 'Content-Type': 'application/json' }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": final_prompt}],
        "temperature": 0.1,
    }

    print("[*] 正在调用DeepSeek API进行智能排程...")
    
    try:
        # d. 发送请求
        response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(data), timeout=120) # 延长超时时间
        response.raise_for_status()
        
        # e. 提取并解析结果
        api_result = response.json()
        raw_content = api_result['choices'][0]['message']['content']
        print(f"[*] API原始返回: \n{raw_content}")
        
        json_str = raw_content.strip().replace("```json", "").replace("```", "").strip()
        result_dict = json.loads(json_str)
        
        schedule = result_dict.get("schedule_result", [])
        print(f"[*] 排程成功，生成了 {len(schedule)} 个日程项。")
        return schedule

    except Exception as e:
        print(f"❌ 智能排程失败: {e}")
        return None

# --- 模拟运行 ---
if __name__ == "__main__":
    # 1. 模拟我们需要排程的数据
    target_date_for_scheduling = "2025-09-19"
    
    # 这些是数据库里已有的、时间固定的事件
    existing_calendar_events = [
        {"event_name": "团队每日站会", "start_time": "2025-09-19T10:00:00", "end_time": "2025-09-19T10:30:00"},
        {"event_name": "午餐时间", "start_time": "2025-09-19T12:00:00", "end_time": "2025-09-19T13:00:00"},
        {"event_name": "与客户的电话会议", "start_time": "2025-09-19T16:00:00", "end_time": "2025-09-19T16:30:00"}
    ]
    
    # 这些是从数据库里读出来的、还没有安排时间的任务
    tasks_from_db = [
        {"task_name": "完成项目A的详细设计文档", "duration_minutes": 180, "priority": "High"},
        {"task_name": "回复所有未读邮件", "duration_minutes": 45, "priority": "Medium"},
        {"task_name": "准备下周的工作计划PPT", "duration_minutes": 90, "priority": "Medium"},
        {"task_name": "研究新的技术框架", "duration_minutes": 120, "priority": "Low"}
    ]
    
    # 2. 调用我们的核心排程函数
    final_schedule = schedule_tasks(tasks_from_db, existing_calendar_events, target_date_for_scheduling)
    
    # 3. 打印最终的排程结果
    if final_schedule:
        print("\n🎉 智能排程完成！建议的日程表如下：")
        print(json.dumps(final_schedule, indent=2, ensure_ascii=False))