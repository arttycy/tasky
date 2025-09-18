import requests
import json
import datetime
import pytz # 导入时区库
import os  # 导入os模块
from dotenv import load_dotenv  # 导入dotenv库

# --- 1. 配置 ---
# 请将这里替换成你的DeepSeek API Key
# --- 1. 加载环境变量 ---
load_dotenv() # 这行代码会自动寻找并加载 .env 文件中的变量
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


# --- 2. 从环境变量中安全地获取API Key ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# --- 增加一个检查，确保密钥已成功加载 ---
if not DEEPSEEK_API_KEY:
    raise ValueError("启动失败：请在 .env 文件中设置您的 DEEPSEEK_API_KEY")
# 我们为AI准备的“指令说明书” (Prompt Template)
# 注意: 我们用 {current_time} 和 {user_query} 作为占位符
PROMPT_TEMPLATE = """
# 角色
你是一位顶尖的智能任务解析专家。

# 任务
分析用户输入的文本，提取以下字段，并以一个JSON对象的格式返回：
- `task_name` (String): 任务的核心名称。
- `start_time` (String): 任务的开始时间，以ISO 8601格式 (`YYYY-MM-DDTHH:MM:SS`) 表示。
- `end_time` (String): 任务的结束时间，以ISO 8601格式表示。
- `duration_minutes` (Integer): 任务的持续时长（分钟）。如果用户未提供，请根据任务内容进行合理估算。
- `priority` (String): 任务优先级。映射为'High', 'Medium', 'Low'。规则：重要且紧急 -> High；重要不紧急 或 紧急不重要 -> Medium；不重要不紧急 -> Low。
- `details` (String): 任务的补充细节描述。
- `location` (String): 任务发生的地点。

# 关键指令
- **时间基准**: 严格以我提供的上下文时间 {current_time} 作为当前时间基准，来进行所有时间推断。
- **输出格式**: 必须，且只能返回一个由```json ... ```代码块包裹的、格式完全正确的JSON对象。
- **空值处理**: 如果用户输入中缺少某个可选字段的信息，请在JSON中省略该字段或将其值设为null。

# 示例
用户输入: "明天下午三点提醒我和李总开个重要的会，大概一个半小时，在三号会议室讨论下个季度的规划。"
你的输出:
```json
{
  "task_name": "和李总开会",
  "start_time": "2025-09-19T15:00:00",
  "end_time": "2025-09-19T16:30:00",
  "duration_minutes": 90,
  "priority": "Medium",
  "details": "讨论下个季度的规划。",
  "location": "三号会议室"
}
"""


def parse_task(user_query):
    """解析用户输入的任务信息"""
    # a. 获取当前时间并格式化 (我们自己搞定时间)
    tz = pytz.timezone('Asia/Shanghai') # 设置为东八区
    current_time_str = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[*] 当前参考时间: {current_time_str}")

    # b. 格式化最终的Prompt
    final_prompt = PROMPT_TEMPLATE.format(current_time=current_time_str, user_query=user_query)

    # c. 准备API请求
    headers = {
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": final_prompt}
        ],
        "temperature": 0.1, # 设置较低的温度以保证输出格式稳定
        "stream": False
    }

    print("[*] 正在调用DeepSeek API...")

    try:
        # d. 发送请求
        response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(data), timeout=60)
        response.raise_for_status()
        
        # e. 提取并解析结果
        api_result = response.json()
        raw_content = api_result['choices'][0]['message']['content']
        print(f"[*] API原始返回: \n{raw_content}")
        
        # 从返回的Markdown代码块中提取纯JSON部分
        json_str = raw_content.strip().replace("```json", "").replace("```", "").strip()
        
        # 将JSON字符串转换成Python字典
        task_dict = json.loads(json_str)
        
        return task_dict

    except requests.exceptions.RequestException as e:
        print(f"❌ API请求失败: {e}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ 解析API返回结果失败: {e}")
        return None


if __name__ == "__main__":
    # 示例用法
    user_input = input("请输入您的任务描述: ")
    result = parse_task(user_input)
    if result:
        print("\n解析结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("任务解析失败")


    