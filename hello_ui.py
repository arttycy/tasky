import streamlit as st

st.set_page_config(page_title="Tasky 助手", layout="wide")

st.title("📝 Tasky - 你的智能任务助手")

# 任务输入区
new_task_input = st.text_input("在这里输入你的新任务，然后按回车提交", placeholder="例如：明天下午三点和李总开会")

if new_task_input:
    st.success(f"任务已添加（模拟）：{new_task_input}")
    st.info("下一步我们将在这里调用AI进行解析...")

st.header("我的任务列表")
# 这里未来会用真实数据替换
st.checkbox("完成项目A的设计文档 (模拟)")
st.checkbox("准备下周工作计划PPT (模拟)", value=True) # value=True 代表已完成