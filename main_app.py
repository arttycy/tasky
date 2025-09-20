# main_app.py

import streamlit as st
import database_manager
import task_parser
import os
import task_decomposer
from datetime import datetime

# 获取当前文件所在的文件夹的绝对路径
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 构造数据库文件的绝对路径
DB_PATH = os.path.join(_CURRENT_DIR, 'tasky.db')

# 后面我们还会导入 task_decomposer 和 task_scheduler

# --- 新增：确保数据库和表在应用启动时已准备就绪 ---
database_manager.init_db()

# --- 页面基础配置 ---
st.set_page_config(
    page_title="Tasky 智能任务助手",
    page_icon="📝",
    layout="wide"
)

# --- 核心功能函数 ---
# main_app.py 文件中的 refresh_tasks 函数

# main_app.py 文件中

# main_app.py 文件中
# main_app.py 文件中

# main_app.py 文件中

def refresh_tasks():
    """
    从数据库获取任务，智能地分为“待办”和“已完成”两部分进行显示，
    并保留父子任务的层级结构。
    """
    
    all_tasks = database_manager.get_all_tasks()
    
    # 1. 数据准备：将任务按ID索引，并分离父子任务
    tasks_by_id = {task['id']: task for task in all_tasks}
    parent_tasks = [task for task in all_tasks if task['parent_task_id'] is None]
    child_tasks = [task for task in all_tasks if task['parent_task_id'] is not None]

    # 2. 渲染“待办任务”区域
    st.header("🎯 待办任务")
    
    # 筛选出真正需要显示在待办列表的主任务
    pending_parent_tasks = [pt for pt in parent_tasks if pt['status'] == 'pending']
    
    if not pending_parent_tasks and not any(ct['status'] == 'pending' for ct in child_tasks):
        st.success("所有任务都已完成！🎉")
    else:
        for task in parent_tasks:
            # 只显示状态为'pending'的主任务
            if task['status'] == 'pending':
                # 找到这个主任务所有'pending'状态的子任务
                pending_children = [ct for ct in child_tasks if ct['parent_task_id'] == task['id'] and ct['status'] == 'pending']
                
                # ... (显示主任务的代码，和之前一样) ...
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                with col1:
                    # 1. 先准备好要显示的详情字符串
                    info_parts = []
                    if task.get('start_time'):
                        try:
                            dt_object = datetime.fromisoformat(task['start_time'])
                            friendly_time = dt_object.strftime('%m月%d日 %H:%M')
                            info_parts.append(f"⏰ {friendly_time}")
                        except (ValueError, TypeError): pass
                    if task.get('duration_minutes'):
                        info_parts.append(f"⏳ 预计耗时: {task.get('duration_minutes')} 分钟")
                    if task.get('location'):
                        info_parts.append(f"📍 {task.get('location')}")
                    
                    details_string = " | ".join(info_parts)
                    
                    # 2. 将任务名称和详情合并成一个Markdown标签
                    # 我们使用HTML的 <br> 来换行，用 <small> 标签来创建灰色的小字体
                    label_markdown = f"""
                    **{task['task_name']}**<br>
                    <small style="color: grey;">{details_string}</small>
                    """
                st.checkbox(
                    label=label_markdown,
                    value=(task['status'] == 'completed'),
                    key=f"check_{task['id']}",
                    on_change=database_manager.update_task_status,
                    args=(task['id'], 'completed' if task['status'] == 'pending' else 'pending'),
                    unsafe_allow_html=True # <-- 必须添加这个参数！
                )

                    # ... (显示时间、地点、详情的代码) ...
                if task.get('start_time'):
                    try:
                        dt_object = datetime.fromisoformat(task['start_time'])
                        friendly_time = dt_object.strftime('%m月%d日 %H:%M')
                        info_parts.append(f"⏰ {friendly_time}")
                    except (ValueError, TypeError): pass
                if task.get('duration_minutes'):
                    info_parts.append(f"⏳ 预计耗时: {task.get('duration_minutes')} 分钟")
                if task.get('location'):
                    info_parts.append(f"📍 {task.get('location')}")
                if info_parts:
                    st.caption(" | ".join(info_parts))
                if task.get('details'):
                    with st.expander("查看详情..."):
                        st.markdown(f"> {task.get('details')}")
                # ---------------------------------
                with col2:
                    if task['duration_minutes'] and task['duration_minutes'] > 600 and not any(c['parent_task_id'] == task['id'] for c in child_tasks):
                        if st.button("智能分解", key=f"decompose_{task['id']}"): pass
                with col3:
                    st.info(f"优先级: {task['priority']}")
                
                # 显示这个主任务下所有'pending'的子任务
                for child in pending_children:
                    st.checkbox(
                        label=f"↳ __{child['task_name']}__", 
                        value=False, key=f"check_pending_{child['id']}", 
                        on_change=database_manager.update_task_status, 
                        args=(child['id'], 'completed')
                        )
                
                st.divider()

    # 3. 渲染“已完成的任务”区域
    completed_tasks = [t for t in all_tasks if t['status'] == 'completed']
    if completed_tasks:
        with st.expander(f"✅ 已完成的任务 ({len(completed_tasks)})", expanded=True): # 默认展开
            
            # 找到所有需要在这个区域显示的父任务
            # 包括：自身已完成的父任务，或者有已完成子任务的父任务
            parent_ids_in_completed = set(
                [t['id'] for t in parent_tasks if t['status'] == 'completed'] + 
                [t['parent_task_id'] for t in child_tasks if t['status'] == 'completed']
            )

            for parent_id in sorted(list(parent_ids_in_completed)):
                parent_task = tasks_by_id.get(parent_id)
                if not parent_task: continue

                # 显示父任务（无论其自身状态如何）
                st.checkbox(
                    label=f"~~_{parent_task['task_name']}_~~" if parent_task['status'] == 'completed' else f"**{parent_task['task_name']}** (有已完成子项)",
                    value=(parent_task['status'] == 'completed'),
                    key=f"check_completed_{parent_task['id']}",
                    on_change=database_manager.update_task_status,
                    args=(parent_task['id'], 'pending' if parent_task['status'] == 'completed' else 'completed')
                )

                # 找到并显示这个父任务下所有'completed'的子任务
                completed_children = [ct for ct in child_tasks if ct['parent_task_id'] == parent_id and ct['status'] == 'completed']
                for child in completed_children:
                    st.checkbox(
                        label=f"↳ ~~_{child['task_name']}_~~",
                        value=True,
                        key=f"check_completed_{child['id']}",
                        on_change=database_manager.update_task_status,
                        args=(child['id'], 'pending')
                    )


# --- 主界面 ---
st.title("📝 Tasky - 你的智能任务助手")
st.markdown("你好！有什么新任务吗？请在下面输入，Tasky会智能解析并为你安排。")

# 任务输入区
with st.form("new_task_form", clear_on_submit=True):
    new_task_input = st.text_input("✨ 在这里输入你的新任务", placeholder="例如：明天下午三点和李总开会，讨论Q4规划")
    submitted = st.form_submit_button("添加任务")

    if submitted and new_task_input:
        with st.spinner("🧠 正在调用AI大脑解析任务..."):
            # 1. 调用任务解析器
            parsed_json = task_parser.parse_task_with_llm(new_task_input)
        
        if parsed_json:
            st.success("任务解析成功！")
            # 2. 将解析结果存入数据库
            database_manager.add_task_from_dify(parsed_json)
        else:
            st.error("抱歉，任务解析失败，请换一种方式描述。")

# --- 全局智能功能区 ---
st.sidebar.title("智能规划中心")
if st.sidebar.button("🤖 一键智能排程"):
    with st.spinner("🗓️ 正在为您规划最优日程..."):
        # 这里未来会调用 task_scheduler
        st.success("日程已智能优化！（功能待实现）")


# --- 刷新并显示任务列表 ---
refresh_tasks()

