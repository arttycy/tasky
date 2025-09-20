# Tasky 智能任务助手

Tasky 是一个智能任务管理工具，能够帮助用户自动解析、分解和安排任务。

## 功能特点

- **自然语言任务输入**：用户可以用自然语言描述任务，Tasky 会自动解析任务的详细信息
- **智能任务分解**：对于复杂的任务，Tasky 可以将其分解为更小的子任务
- **智能日程安排**：根据任务的优先级和时长，自动安排最优的日程表
- **可视化界面**：基于 Streamlit 的用户界面，方便查看和管理任务

## 项目结构

```
tasky_demo/
├── app.py                 # 主应用逻辑和排程功能
├── main_app.py            # Streamlit 用户界面
├── database_manager.py    # 数据库管理模块
├── task_parser.py         # 任务解析模块
├── task_decomposer.py        # 任务分解模块
├── task_scheduler.py      # 任务排程模块
├── tasky.db              # SQLite 数据库文件
└── .env                  # 环境变量配置文件
```

## 安装和配置

1. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

2. 创建 `.env` 文件并配置 DeepSeek API Key：
   ```
   DEEPSEEK_API_KEY=your_api_key_here
   ```

## 模块说明

### app.py
主应用文件，包含测试数据设置和智能排程逻辑。

### main_app.py
Streamlit 用户界面，提供任务输入和展示功能。

### database_manager.py
数据库管理模块，负责与 SQLite 数据库交互，包括：
- 初始化数据库
- 添加任务和子任务
- 查询固定事件和灵活任务
- 更新任务日程和状态

### task_parser.py
任务解析模块，使用 DeepSeek API 将自然语言任务描述解析为结构化数据。

### task_decomposer.py
任务分解模块，将复杂任务分解为具体的子任务。

### task_scheduler.py
任务排程模块，根据任务优先级和时长智能安排日程。

## 使用方法

1. 运行 Streamlit 界面：
   ```
   streamlit run main_app.py
   ```

2. 或者运行命令行版本：
   ```
   python app.py
   ```

## API 配置

本项目使用 DeepSeek API 进行自然语言处理，需要在 `.env` 文件中配置 API Key。

## 数据库结构

任务表包含以下字段：
- id: 任务ID
- task_name: 任务名称
- start_time: 开始时间
- end_time: 结束时间
- duration_minutes: 持续时间（分钟）
- priority: 优先级（High/Medium/Low）
- status: 状态（pending/completed）
- details: 详细描述
- location: 地点
- parent_task_id: 父任务ID（用于子任务）
- created_at: 创建时间

## 开发计划

- [ ] 完善任务分解功能
- [ ] 完善智能排程功能
- [ ] 添加任务提醒功能
- [ ] 支持更多AI模型