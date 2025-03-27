import streamlit as st
import pandas as pd
import sqlite3
from collections import Counter
import os

def convert_db():
    def process_file(file_path):
        # 使用 pandas 读取 Excel 文件
        merged_df = pd.read_excel(file_path)

        # 将 '发表时间' 列转换为日期格式
        merged_df['发表时间'] = pd.to_datetime(merged_df['发表时间'].astype(str), format='%Y%m%d').dt.strftime('%Y-%m-%d')

        # 统计每个分类的条目数
        category_counts = Counter()
        for categories in merged_df['分类']:
            for category in categories.split(', '):
                category_counts[category] += 1

        # 排序分类
        sorted_categories = sorted(
            category_counts.items(),
            key=lambda x: (-x[1], x[0])  # 按条目数降序，分类名升序排序
        )

        # 确保 Others 排在最后
        sorted_categories = [cat for cat in sorted_categories if cat[0] != 'Others'] + [('Others', 0)]

        # 为每个分类分配顺序
        category_order = {category: idx for idx, (category, _) in enumerate(sorted_categories)}

        # 按分类顺序对 DataFrame 排序
        def get_category_order(categories):
            orders = [category_order[category] for category in categories.split(', ') if category in category_order]
            return min(orders) if orders else len(category_order)  # 默认排序到最后

        merged_df['分类顺序'] = merged_df['分类'].apply(get_category_order)
        merged_df = merged_df.sort_values(by='分类顺序').drop(columns=['分类顺序'])

        # 获取输出文件路径
        output_dir = os.path.dirname(file_path)
        db_path = os.path.join(output_dir, 'content_database.sqlite')

        # 创建 SQLite 数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 清空已有表并重新创建表
        cursor.execute('DROP TABLE IF EXISTS content')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            title TEXT,
            url TEXT,
            publish_date TEXT
        )
        ''')

        # 插入数据
        data_to_insert = []
        for _, row in merged_df.iterrows():
            categories = row['分类'].split(', ')
            for category in categories:
                data_to_insert.append((category, row['内容标题'], row['内容url'], row['发表时间']))

        # 按分类顺序插入
        data_to_insert = sorted(data_to_insert, key=lambda x: (category_order[x[0]], x[1]))
        cursor.executemany('''
        INSERT INTO content (category, title, url, publish_date) VALUES (?, ?, ?, ?)
        ''', data_to_insert)

        # 提交更改并关闭数据库连接
        conn.commit()
        conn.close()

        return db_path

    # Streamlit 应用
    st.title('Excel 转 SQLite 数据库')

    # 文件上传
    uploaded_file = st.file_uploader("选择 Excel 文件", type=["xlsx"])

    if uploaded_file:
        # 显示上传的文件名
        st.write(f"已选择文件: {uploaded_file.name}")

        # 按钮触发转换
        if st.button('转换'):
            with st.spinner('处理中...'):
                try:
                    # 保存上传的文件
                    file_path = os.path.join("temp", uploaded_file.name)
                    os.makedirs("temp", exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # 执行转换并获取生成的 SQLite 数据库路径
                    db_path = process_file(file_path)

                    # 显示成功信息
                    st.success(f"数据库已生成！内容已按分类条目数排序，保存为 {db_path}")

                    # 提供下载按钮
                    with open(db_path, "rb") as file:
                        st.download_button(
                            label="下载转换后的数据库",
                            data=file,
                            file_name=os.path.basename(db_path),
                            mime="application/x-sqlite3"
                        )

                except Exception as e:
                    st.error(f"发生错误: {e}")
