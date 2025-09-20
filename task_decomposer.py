"""
任务分解模块

该模块提供了一个函数，用于将复杂的任务分解为更小的子任务。
使用DeepSeek API进行自然语言处理，提取任务的关键信息。
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# --- 升级版Prompt，要求返回更丰富的信息 ---
PROMPT_TEMPLATE = """
# 角色
你是一位世界级的项目管理专家（PMP）和SOP（标准作业程序）撰写大师。

# 任务
我会给你一个比较宏观或复杂的任务名称。请你将其分解成一个由3到7个具体的、按逻辑顺序排列的、可执行的子任务列表。
对于每一个子任务，请评估它的**预估时长（分钟）**和**优先级**。

# 关键指令
- 每个子任务都应该是动词开头的短语，清晰明确。
- 你的输出必须，且只能是一个JSON对象，该对象只包含一个键 "sub_tasks"，其值为一个**对象数组**。
- 数组中的每个对象都必须包含以下三个键: `task_name` (String), `duration_minutes` (Integer), `priority` (String: 'High', 'Medium', 'Low')。
- 不要返回任何额外的解释或文字。

# 示例
输入: "完成第四季度市场分析报告"
输出:
```json
{{
  "sub_tasks": [
    {{ "task_name": "收集第一方销售数据和用户反馈", "duration_minutes": 120, "priority": "High" }},
    {{ "task_name": "调研三个主要竞品的最新动态", "duration_minutes": 180, "priority": "High" }},
    {{ "task_name": "分析宏观市场趋势和行业报告", "duration_minutes": 90, "priority": "Medium" }},
    {{ "task_name": "撰写报告初稿并进行数据可视化", "duration_minutes": 240, "priority": "High" }},
    {{ "task_name": "与相关部门评审并修改报告", "duration_minutes": 60, "priority": "Medium" }},
    {{ "task_name": "完成报告终稿并归档", "duration_minutes": 30, "priority": "Low" }}
  ]
}}
}}

需要分解的任务: {complex_task_name}
"""

def decompose_task(task_name: str):
    """接收一个复杂任务的名称，返回一个包含子任务详情（字典）的列表。
    
    Args:
        task_name (str): 复杂任务的名称
        
    Returns:
        list: 包含子任务详情的字典列表，如果分解失败则返回None
    """
    print(f"[*] 接收到分解请求，任务: '{task_name}'")
    # 注意：这里需要对JSON示例中的花括号进行转义
    final_prompt = PROMPT_TEMPLATE.format(complex_task_name=task_name)

    headers = {
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": final_prompt}],
        "temperature": 0.2
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(data), timeout=60)
        response.raise_for_status()
        
        api_result = response.json()
        raw_content = api_result['choices'][0]['message']['content']
        
        json_str = raw_content.strip().replace("```json", "").replace("```", "").strip()
        result_dict = json.loads(json_str)
        
        sub_tasks = result_dict.get("sub_tasks", [])
        print(f"[*] 分解成功，得到 {len(sub_tasks)} 个子任务。")
        return sub_tasks

    except Exception as e:
        print(f"任务分解失败: {e}")
        return None


if __name__ == "__main__":
    # 测试
    sample_task = "策划并举办一次公司年度技术分享会"
    sub_tasks_list = decompose_task(sample_task)
    if sub_tasks_list:
        print("\n--- 分解结果 (结构化数据) ---")
        print(json.dumps(sub_tasks_list, indent=2, ensure_ascii=False))
