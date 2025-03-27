# main.py
import streamlit as st
from convert_db import convert_db

st.set_page_config(page_title="数据酷转换", page_icon="✨")

def main():
    st.sidebar.title("功能选择")
    # 将页面名称映射到对应的函数
    page_names_to_funcs = {
        "数据酷转换": convert_db,

    }

    demo_name = st.sidebar.selectbox("选择一个演示", list(page_names_to_funcs.keys()))
    # 根据选定的演示执行相应的函数
    page_function = page_names_to_funcs[demo_name]
    page_function()

if __name__ == "__main__":
    main()