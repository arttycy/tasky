# main_app.py

import streamlit as st
import database_manager
import task_parser
import os
import task_decomposer
import task_scheduler
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
def refresh_tasks():
    """
    从数据库获取任务，智能地分为“待办”和“已完成”两部分进行显示，
    并保留父子任务的层级结构。修正了列布局和缩进问题，确保所有渲染
    都在对应的 with colX: 块内。
    """
    all_tasks = database_manager.get_all_tasks()

    # 组织任务
    tasks_by_id = {task['id']: task for task in all_tasks}
    parent_tasks = [task for task in all_tasks if task['parent_task_id'] is None]
    child_tasks = [task for task in all_tasks if task['parent_task_id'] is not None]

    # --- 待办任务 区 ---
    st.header("🎯 待办任务")

    pending_parent_tasks = [pt for pt in parent_tasks if pt['status'] == 'pending']
    pending_children_exist = any(ct['status'] == 'pending' for ct in child_tasks)

    if not pending_parent_tasks and not pending_children_exist:
        st.success("所有任务都已完成！🎉")
    else:
        for task in pending_parent_tasks:
            # 找到该父任务下的 pending 子任务
            pending_children = [ct for ct in child_tasks if ct['parent_task_id'] == task['id'] and ct['status'] == 'pending']
            child_tasks_of_parent = [c for c in child_tasks if c['parent_task_id'] == task['id']]

            # 三列布局：任务主体 / 完成勾选 / 优先级
            col1, col2, col3 = st.columns([6, 1, 2])
            with col1:
                # 组装详情字符串
                info_parts = []
                if task.get('start_time'):
                    try:
                        dt_object = datetime.fromisoformat(task['start_time'])
                        friendly_time = dt_object.strftime('%m月%d日 %H:%M')
                        info_parts.append(f"⏰ {friendly_time}")
                    except (ValueError, TypeError):
                        pass
                if task.get('duration_minutes'):
                    info_parts.append(f"⏳ 预计耗时: {task.get('duration_minutes')} 分钟")
                if task.get('location'):
                    info_parts.append(f"📍 {task.get('location')}")
                details_string = " | ".join(info_parts)

                # 任务名称 + 详情（放在 col1 内）
                label_markdown = f"""**{task.get('task_name', '未命名任务')}**  <small style="color: grey;">{details_string}</small>"""
                st.markdown(label_markdown, unsafe_allow_html=True)

                # 详情展开
                if task.get('details'):
                    with st.expander("查看详情..."):
                        st.markdown(f"> {task.get('details')}")

            with col2:
                # 把完成 checkbox 放在中间列（隐藏 label）
                st.checkbox(
                    label="",
                    value=(task.get('status') == 'completed'),
                    key=f"check_parent_{task['id']}",
                    on_change=database_manager.update_task_status,
                    args=(task['id'], 'completed' if task.get('status') == 'pending' else 'pending'),
                    label_visibility="collapsed"
                )
            with col2:
                # --- ↓↓↓ 为“智能分解”按钮注入真实功能 ↓↓↓ ---
                if task['duration_minutes'] and task['duration_minutes'] > 600 and not child_tasks_of_parent:
                    if st.button("智能分解", key=f"decompose_{task['id']}"):
                        with st.spinner("🧠 正在调用AI大脑进行智能分解..."):
                            # 1. 调用任务分解器AI大脑
                            sub_tasks_list = task_decomposer.decompose_task(task['task_name'])
                            
                            # 2. 如果成功，将子任务列表存入数据库
                            if sub_tasks_list:
                                database_manager.add_subtasks(task['id'], sub_tasks_list)
                                st.success("任务分解成功！")
                                # 3. 强制刷新页面，以立刻显示出新的子任务
                                st.rerun()
                            else:
                                st.error("抱歉，AI未能成功分解任务。")
                # ------------------------------------

            with col3:
                st.info(f"优先级: {task.get('priority', 'Low')}")

            # 显示 pending 子任务（缩进显示）
            for child in pending_children:
                c1, c2 = st.columns([0.04, 0.96])
                with c1:
                    st.checkbox(
                        label="",
                        value=(child.get('status') == 'completed'),
                        key=f"check_child_{child['id']}",
                        on_change=database_manager.update_task_status,
                        args=(child['id'], 'completed' if child.get('status') == 'pending' else 'pending'),
                        label_visibility="collapsed"
                    )
                with c2:
                    st.markdown(f"↳ **{child.get('task_name', '未命名子任务')}**")
            st.divider()

    # --- 已完成任务区 ---
    completed_tasks = [t for t in all_tasks if t['status'] == 'completed']
    if completed_tasks:
        with st.expander(f"✅ 已完成的任务 ({len(completed_tasks)})", expanded=True):
            # 需要在已完成区显示的父任务集合：
            parent_ids_in_completed = set(
                [t['id'] for t in parent_tasks if t['status'] == 'completed'] +
                [t['parent_task_id'] for t in child_tasks if t['status'] == 'completed']
            )

            for parent_id in sorted(list(parent_ids_in_completed)):
                parent_task = tasks_by_id.get(parent_id)
                if not parent_task:
                    continue

                # 父任务的一行（父任务可能本身是 completed，也可能只是有已完成子项）
                p_col1, p_col2 = st.columns([9, 1])
                with p_col1:
                    if parent_task.get('status') == 'completed':
                        st.markdown(f"~~_{parent_task.get('task_name', '未命名任务')}_~~")
                    else:
                        st.markdown(f"**{parent_task.get('task_name', '未命名任务')}** (有已完成子项)")

                with p_col2:
                    st.checkbox(
                        label="",
                        value=(parent_task.get('status') == 'completed'),
                        key=f"check_completed_parent_{parent_task['id']}",
                        on_change=database_manager.update_task_status,
                        args=(parent_task['id'], 'pending' if parent_task.get('status') == 'completed' else 'completed'),
                        label_visibility="collapsed"
                    )

                # 显示该父任务下所有 completed 的子任务
                completed_children = [ct for ct in child_tasks if ct['parent_task_id'] == parent_id and ct['status'] == 'completed']
                for child in completed_children:
                    c1, c2 = st.columns([0.04, 0.96])
                    with c1:
                        st.checkbox(
                            label="",
                            value=True,
                            key=f"check_completed_child_{child['id']}",
                            on_change=database_manager.update_task_status,
                            args=(child['id'], 'pending'),
                            label_visibility="collapsed"
                        )
                    with c2:
                        st.markdown(f"↳ ~~_{child.get('task_name', '未命名子任务')}_~~")
            # end for parent_id

# --- 主界面 ---
st.title("📝 Tasky - 你的智能任务助手")
st.markdown("你好！有什么新任务吗？请在下面输入，Tasky会智能解析并为你安排。")

# 任务输入区
with st.form("new_task_form", clear_on_submit=True):
    new_task_input = st.text_input("✨ 在这里输入你的新任务", placeholder="例如：明天下午三点和李总开会，讨论Q4规划")
    submitted = st.form_submit_button("添加任务")

    if submitted and new_task_input:
        with st.spinner("🧠 正在调用AI大脑解析任务..."):
                parsed_json = task_parser.parse_task_with_llm(new_task_input)
                if parsed_json:
                    database_manager.add_task_from_dify(parsed_json)
                    st.success("任务解析成功！")
                else:
                    st.error("抱歉，任务解析失败，请换一种方式描述。")



# --- 全局智能功能区 ---
st.sidebar.title("智能规划中心")
if st.sidebar.button("🤖 一键智能排程"):
    with st.spinner("🗓️ 正在为您规划最优日程..."):

        # --- ↓↓↓ 这是新增的核心逻辑 ↓↓↓ ---
        # 1. 定义排程的目标日期（这里我们先简单设为今天）
        target_date = datetime.now().strftime('%Y-%m-%d')

        # 2. 从数据库获取所需信息
        print(f"[*] 开始为日期 {target_date} 进行智能排程...")
        fixed_events = database_manager.get_fixed_events(target_date)
        flexible_tasks = database_manager.get_flexible_tasks()

        if not flexible_tasks:
            st.sidebar.warning("没有需要排程的灵活任务。")
        else:
            # 3. 调用智能排程器AI大脑
            # 我们需要从灵活任务中提取特定字段给AI
            tasks_for_ai = [
                {"task_name": t["task_name"], "duration_minutes": t["duration_minutes"], "priority": t["priority"]}
                for t in flexible_tasks
            ]
            schedule_result = task_scheduler.schedule_tasks(tasks_for_ai, fixed_events, target_date)

            # 4. 如果成功，将排程结果写回数据库
            if schedule_result:
                task_name_to_id_map = {t["task_name"]: t["id"] for t in flexible_tasks}

                success_count = 0
                for scheduled_item in schedule_result:
                    task_name = scheduled_item.get("task_name")
                    if task_name in task_name_to_id_map:
                        task_id = task_name_to_id_map[task_name]
                        start_time = scheduled_item.get("start_time")
                        end_time = scheduled_item.get("end_time")

                        if database_manager.update_task_schedule(task_id, start_time, end_time):
                            success_count += 1

                st.sidebar.success(f"成功优化了 {success_count} 个任务的日程！")
                st.rerun() # 刷新主页面以显示新日程
            else:
                st.sidebar.error("抱歉，AI排程失败。")
        # --- 核心逻辑结束 ---

# --- 刷新并显示任务列表 ---
refresh_tasks()
