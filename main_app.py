# main_app.py (V1.5 - 修正了表单内的按钮错误)

import streamlit as st
import database_manager
import task_parser
import task_decomposer
import task_scheduler
from datetime import datetime
import os

# --- 1. 页面基础配置 (必须是第一个st命令) ---
st.set_page_config(
    page_title="Tasky 智能任务助手",
    page_icon="📝",
    layout="wide"
)

# --- 2. 注入自定义CSS来优化间距 ---
st.markdown("""
    <style>
    /* 减小checkbox和下方元素的间距 */
    div[data-testid="stVerticalBlock"] div[data-testid="stCheckbox"] {
        padding-bottom: 0px;
        margin-bottom: -10px;
    }
    /* 减小按钮的内边距和字体大小，让图标按钮更精致 */
    div[data-testid="stHorizontalBlock"] button {
        padding: 0.15rem 0.4rem; /* 调整垂直和水平内边距 */
        font-size: 0.75rem;      /* 减小字体大小以缩小图标 */
        line-height: 1.3;        /* 调整行高以优化垂直对齐 */
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 初始化数据库和会话状态 ---
database_manager.init_db()

if 'editing_task_id' not in st.session_state:
    st.session_state.editing_task_id = None
if 'confirming_delete_id' not in st.session_state:
    st.session_state.confirming_delete_id = None

# --- 4. 辅助函数 (处理交互逻辑) ---

def handle_delete(task_id):
    """删除按钮 on_click 的回调函数"""
    database_manager.delete_task(task_id)
    st.session_state.confirming_delete_id = None


# --- 5. 核心渲染函数 ---

def display_task_item(task, all_child_tasks):
    """一个通用的函数，用来显示任何一个任务项（无论父子）"""
    task_id = task['id']
    is_parent = task['parent_task_id'] is None
    is_completed = (task['status'] == 'completed')

    # --- A. 编辑模式 ---
    if st.session_state.editing_task_id == task_id:
        with st.form(key=f"edit_form_{task_id}"):
            st.markdown(f"**正在编辑: {task['task_name']}**")
            new_name = st.text_input("任务名称", value=task['task_name'])
            new_details = st.text_area("任务详情", value=task.get('details', ''))
            
            # 表单的提交和取消按钮
            col_save, col_cancel = st.columns(2)
            with col_save:
                # 定义保存按钮
                save_button_pressed = st.form_submit_button("✔️ 保存", use_container_width=True)
            with col_cancel:
                 # 将取消按钮也定义为提交按钮
                 cancel_button_pressed = st.form_submit_button("✖️ 取消", use_container_width=True)

        # 在表单外部处理逻辑
        if save_button_pressed:
            database_manager.update_task_name(task_id, new_name)
            database_manager.update_task_details(task_id, new_details)
            st.session_state.editing_task_id = None
            st.rerun()
        
        if cancel_button_pressed:
            st.session_state.editing_task_id = None
            st.rerun()
        return

    # --- B. 删除确认模式 ---
    if st.session_state.confirming_delete_id == task_id:
        st.warning(f"确定要删除任务 '{task['task_name']}' 吗？此操作不可撤销！")
        col_confirm, col_cancel_del = st.columns(2)
        with col_confirm:
            st.button("确认删除", key=f"confirm_delete_{task_id}", on_click=handle_delete, args=(task_id,), use_container_width=True)
        with col_cancel_del:
            if st.button("取消", key=f"cancel_delete_{task_id}", use_container_width=True):
                st.session_state.confirming_delete_id = None
                st.rerun()
        return

    # --- C. 正常显示模式 ---
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        prefix = "" if is_parent else "↳ "
        
        if is_completed:
            label_text = f"~~_{prefix}{task['task_name']}_~~"
        else:
            label_text = f"**{prefix}{task['task_name']}**" if is_parent else f"{prefix}__{task['task_name']}__"

        st.checkbox(
            label=label_text,
            value=is_completed,
            key=f"check_{task_id}",
            on_change=database_manager.update_task_status,
            args=(task_id, 'pending' if is_completed else 'completed')
        )
        
        if is_parent:
            info_parts = []
            if task.get('start_time'):
                try:
                    dt = datetime.fromisoformat(task['start_time'])
                    info_parts.append(f"⏰ {dt.strftime('%m月%d日 %H:%M')}")
                except (ValueError, TypeError): pass
            if task.get('duration_minutes'):
                info_parts.append(f"⏳ {task.get('duration_minutes')} 分钟")
            if task.get('location'):
                info_parts.append(f"📍 {task.get('location')}")
            if info_parts:
                st.caption(" | ".join(info_parts))
            if task.get('details'):
                with st.expander("查看详情..."):
                    st.markdown(f"> {task.get('details')}")

    with col2:
        if not is_completed: # 只为待办任务显示按钮
            btn_cols = st.columns(3)
            with btn_cols[0]:
                if st.button("✏️", key=f"edit_{task_id}", help="编辑"):
                    st.session_state.editing_task_id = task_id
                    st.rerun()
            with btn_cols[1]:
                if st.button("🗑️", key=f"delete_{task_id}", help="删除"):
                    st.session_state.confirming_delete_id = task_id
                    st.rerun()
            with btn_cols[2]:
                 task_children = [c for c in all_child_tasks if c['parent_task_id'] == task_id]
                 if is_parent and task['duration_minutes'] and task['duration_minutes'] > 90 and not task_children:
                    if st.button("🧬", key=f"decompose_{task_id}", help="智能分解"):
                        with st.spinner("🧠 ..."):
                            sub_tasks = task_decomposer.decompose_task(task['task_name'])
                            if sub_tasks:
                                database_manager.add_subtasks(task_id, sub_tasks)
                                st.rerun()
                            else:
                                st.error("分解失败")


def refresh_tasks():
    all_tasks = database_manager.get_all_tasks()
    tasks_by_id = {task['id']: task for task in all_tasks}
    parent_tasks = [t for t in all_tasks if t['parent_task_id'] is None]
    child_tasks = [t for t in all_tasks if t['parent_task_id'] is not None]

    st.header("🎯 待办任务")
    pending_tasks = [t for t in all_tasks if t['status'] == 'pending']
    if not pending_tasks:
        st.success("所有任务都已完成！🎉")
    else:
        pending_parent_tasks = [pt for pt in parent_tasks if pt['status'] == 'pending']
        for task in pending_parent_tasks:
            display_task_item(task, child_tasks)
            pending_children = [ct for ct in child_tasks if ct['parent_task_id'] == task['id'] and ct['status'] == 'pending']
            for child in pending_children:
                display_task_item(child, child_tasks)
            st.divider()

    st.header("✅ 已完成的任务")
    completed_tasks = [t for t in all_tasks if t['status'] == 'completed']
    if completed_tasks:
        parent_ids_in_completed = sorted(list(set(
            [t['id'] for t in parent_tasks if t['status'] == 'completed'] +
            [t['parent_task_id'] for t in child_tasks if t['status'] == 'completed']
        )))

        for parent_id in parent_ids_in_completed:
            parent_task = tasks_by_id.get(parent_id)
            if not parent_task: continue

            if parent_task['status'] == 'pending':
                st.markdown(f"**{parent_task['task_name']}** (有已完成子项)")
            else:
                display_task_item(parent_task, child_tasks)
            
            completed_children = [ct for ct in child_tasks if ct['parent_task_id'] == parent_id and ct['status'] == 'completed']
            for child in completed_children:
                display_task_item(child, child_tasks)
            st.divider()
    else:
        st.info("还没有已完成的任务。")


# --- 6. 主界面 ---
st.title("📝 Tasky - 你的智能任务助手")
st.markdown("你好！有什么新任务吗？请在下面输入，Tasky会智能解析并为你安排。")

with st.form("new_task_form", clear_on_submit=True):
    new_task_input = st.text_input("✨ 在这里输入你的新任务", placeholder="例如：明天下午三点和李总开会，讨论Q4规划")
    submitted = st.form_submit_button("添加任务")
    if submitted and new_task_input:
        with st.spinner("🧠 正在调用AI大脑解析任务..."):
            parsed_json = task_parser.parse_task_with_llm(new_task_input)
            if parsed_json:
                database_manager.add_task_from_dify(parsed_json)
                st.rerun()
            else:
                st.error("抱歉，任务解析失败，请换一种方式描述。")

st.sidebar.title("智能规划中心")
if st.sidebar.button("🤖 一键智能排程"):
    target_date = datetime.now().strftime('%Y-%m-%d')
    with st.spinner(f"🗓️ 正在为您规划 {target_date} 的日程..."):
        fixed_events = database_manager.get_fixed_events(target_date)
        flexible_tasks = database_manager.get_flexible_tasks()
        if not flexible_tasks:
            st.sidebar.warning("没有需要排程的灵活任务。")
        else:
            tasks_for_ai = [{"task_name": t["task_name"], "duration_minutes": t["duration_minutes"], "priority": t["priority"]} for t in flexible_tasks]
            schedule_result = task_scheduler.schedule_tasks(tasks_for_ai, fixed_events, target_date)
            if schedule_result:
                task_name_to_id_map = {t["task_name"]: t["id"] for t in flexible_tasks}
                success_count = 0
                for item in schedule_result:
                    name = item.get("task_name")
                    if name in task_name_to_id_map:
                        task_id = task_name_to_id_map[name]
                        if database_manager.update_task_schedule(task_id, item.get("start_time"), item.get("end_time")):
                            success_count += 1
                st.sidebar.success(f"成功优化了 {success_count} 个任务的日程！")
                st.rerun()
            else:
                st.sidebar.error("抱歉，AI排程失败。")

# --- 7. 渲染主函数 ---
refresh_tasks()

