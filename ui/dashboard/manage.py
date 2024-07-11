import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from collections import Counter
import requests


class Manager:
    _mongodb = None
    _chat_collection = None
    _login_collection = None
    _ban_collection = None
    _model_chat = None
    _model_embed = None
    _ip = None
    def __new__(cls, mongo_store, chat_collection, login_collection, ban_collection, model_chat, model_embed, ip):
        if not cls._mongodb:
            cls._mongodb = mongo_store
            cls._chat_collection = chat_collection
            cls._login_collection = login_collection
            cls._ban_collection = ban_collection
            cls._model_chat = model_chat
            cls._model_embed = model_embed
            cls._ip = ip
    @staticmethod
    def calculate_metrics(df):
        if df.empty:
            return {metric: 0 for metric in
                    ['total_questions', 'total_input_words', 'total_output_words', 'avg_processing_time',
                     'max_processing_time']}

        return {
            'total_questions': len(df),
            'total_input_words': df['input_word_count'].sum(),
            'total_output_words': df['output_word_count'].sum(),
            'avg_processing_time': df['processing_time'].mean(),
            'max_processing_time': df['processing_time'].max()
        }

    @staticmethod
    def calc_percent_change(today_value, yesterday_value):
        if yesterday_value == 0:
            return None if today_value == 0 else 100.0
        change = ((today_value - yesterday_value) / yesterday_value) * 100
        return round(change, 1)

    @staticmethod
    def format_delta(percent_change):
        if percent_change is None:
            return "N/A"
        return f"{percent_change:+.1f}%" if percent_change != 0 else "0%"

    @classmethod
    def show(cls):
        data = list(cls._mongodb.find_many(
            cls._chat_collection, {}
        ))
        st.html('<p class="big-font">QUẢN LÝ HỆ THỐNG</p>')

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        login_data = list(cls._mongodb.find_many(cls._login_collection, {}))
        login_df = None
        if login_data:
            login_df = pd.DataFrame(login_data)
            login_df['timestamp'] = pd.to_datetime(login_df['timestamp'])

        # Summary statistics
        st.html('<p class="medium-font">Thống Kê Tổng Quan</p>')
        col1, col2, col3, col4, col5 = st.columns(5)

        # Get today's date and yesterday's date
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        # Filter dataframe for today and yesterday
        df_today = df[df['timestamp'].dt.date == today]
        df_yesterday = df[df['timestamp'].dt.date == yesterday]

        # Calculate metrics for all data, today, and yesterday
        metrics_all = cls.calculate_metrics(df)
        metrics_today = cls.calculate_metrics(df_today)
        metrics_yesterday = cls.calculate_metrics(df_yesterday)

        # Display metrics with percentage change
        col1.metric(
            label="Tổng Số Câu Hỏi",
            value=f"{metrics_all['total_questions']:,}",
            delta=cls.format_delta(
                cls.calc_percent_change(metrics_today['total_questions'], metrics_yesterday['total_questions']))
        )

        col2.metric(
            label="Input",
            value=f"{metrics_all['total_input_words']:,}",
            delta=cls.format_delta(
                cls.calc_percent_change(metrics_today['total_input_words'], metrics_yesterday['total_input_words']))
        )

        col3.metric(
            label="Output",
            value=f"{metrics_all['total_output_words']:,}",
            delta=cls.format_delta(
                cls.calc_percent_change(metrics_today['total_output_words'], metrics_yesterday['total_output_words']))
        )

        col4.metric(
            label="Xử Lý TB (giây)",
            value=f"{metrics_all['avg_processing_time']:.2f}",
            delta=cls.format_delta(
                cls.calc_percent_change(metrics_today['avg_processing_time'], metrics_yesterday['avg_processing_time']))
        )

        col5.metric(
            label="Xử Lý Lâu Nhất (giây)",
            value=f"{metrics_all['max_processing_time']:.2f}",
            delta=cls.format_delta(
                cls.calc_percent_change(metrics_today['max_processing_time'], metrics_yesterday['max_processing_time']))
        )
        # # Visualizations
        st.html('<p class="medium-font">Biểu Đồ Thống Kê</p>')

        # # Line chart for processing times
        fig_line = px.line(df, x='timestamp', y='processing_time', title='Thời Gian Xử Lý Theo Thời Gian')
        fig_line.update_layout(xaxis_title="Thời Gian", yaxis_title="Thời Gian Xử Lý (giây)")
        st.plotly_chart(fig_line, use_container_width=True)

        # IP with most requests
        st.html('<p class="medium-font">IP Gửi Nhiều Request Nhất</p>')

        banned_ips = set(doc['ip'] for doc in cls._mongodb.find_many(cls._ban_collection, {}))

        if login_df is not None and not login_df.empty:
            # Lọc các IP không bị cấm
            non_banned_ips = login_df[~login_df['ip_address'].isin(banned_ips)]['ip_address']
            ip_counts = Counter(non_banned_ips)

            # Chọn số lượng IP muốn hiển thị
            num_ips = st.selectbox("Chọn số lượng IP muốn hiển thị", options=range(1, min(11, len(ip_counts) + 1)),
                                   index=min(4, len(ip_counts) - 1))

            # Lấy top IP
            top_ips = ip_counts.most_common(num_ips)

            # Hiển thị thông tin về top IP
            for ip, count in top_ips:
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(f":red[IP: {ip} (Bạn)]" if ip == cls._ip else f"IP: {ip}")
                col2.write(f"Số lượng: {count}")
                if ip != cls._ip and ip not in banned_ips:
                    if col3.button(f"Ban {ip}", key=f"ban_{ip}"):
                        cls._mongodb.insert_one(cls._ban_collection, {"ip": ip, "banned_at": datetime.now()})
                        st.success(f"Đã ban IP {ip}")
                        st.rerun()

            # Hiển thị biểu đồ cột cho top IP
            ip_df = pd.DataFrame(top_ips, columns=['IP', 'Số lượng truy cập'])
            fig_ip = px.bar(ip_df, x='IP', y='Số lượng truy cập', title=f'Top {num_ips} IP có nhiều truy cập nhất')
            st.plotly_chart(fig_ip, use_container_width=True)

            # Danh sách IP đã bị cấm
            st.markdown('<p class="medium-font">Danh Sách IP Đã Bị Cấm</p>', unsafe_allow_html=True)

            banned_ips_data = list(cls._mongodb.find_many(cls._ban_collection, {}))
            if banned_ips_data:
                banned_df = pd.DataFrame(banned_ips_data)
                banned_df['banned_at'] = pd.to_datetime(banned_df['banned_at'])
                banned_df = banned_df.sort_values('banned_at', ascending=False)

                for _, row in banned_df.iterrows():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    col1.write(f"IP: {row['ip']}")
                    col2.write(f"Bị cấm lúc: {row['banned_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                    if col3.button(f"Gỡ ban", key=f"unban_{row['ip']}"):
                        cls._mongodb.delete_one(cls._ban_collection, {"ip": row['ip']})
                        st.success(f"Đã gỡ cấm IP {row['ip']}")
                        st.rerun()
            else:
                st.write("Không có IP nào bị cấm.")
        else:
            st.write("Không có dữ liệu đăng nhập.")

        st.html('<p class="medium-font">Tìm Kiếm và Lọc</p>')
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("Tìm kiếm câu hỏi")
        with col2:
            date_range = st.date_input("Chọn khoảng thời gian", [datetime.now() - timedelta(days=7), datetime.now()])

        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = df[
                (df['question'].str.contains(search_term, case=False, na=False)) &
                (df['timestamp'].dt.date >= start_date) &
                (df['timestamp'].dt.date <= end_date)
                ]
        else:
            filtered_df = df[df['question'].str.contains(search_term, case=False, na=False)]

        filtered_df_renamed = filtered_df.rename(columns={
            'question': 'Câu Hỏi',
            'answer': 'Câu Trả Lời',
            'timestamp': 'Thời Gian',
            'input_word_count': 'Số Từ Input',
            'output_word_count': 'Số Từ Output',
            'processing_time': 'Thời Gian Xử Lý (giây)'
        })

        st.markdown(f"**Kết quả:** `{len(filtered_df)}` bản ghi")
        st.dataframe(
            filtered_df_renamed[
                ['Câu Hỏi', 'Câu Trả Lời', 'Thời Gian', 'Số Từ Input', 'Số Từ Output', 'Thời Gian Xử Lý (giây)']],
            height=300
        )
        # Database and chatbot information
        st.markdown('<p class="medium-font">Thông Tin Hệ Thống</p>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.info(f"**Vector Store:** Qdrant")
        col3.info(f"**NoSQL Store:** MongoDB")
        col2.info(f"**Chat Model:** {cls._model_chat}")
        st.info(f"**Embedded Model:** {cls._model_embed}")
