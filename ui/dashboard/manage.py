import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from collections import Counter
import plotly.graph_objects as go
import psutil
import platform
import time
import re
class General:
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
        if "data" not in st.session_state:
            st.session_state.data = list(st.session_state.mongodb.find_many(
                st.session_state.chat_collection, {}
            ))

        if "login_data" not in st.session_state:
            st.session_state.login_data = list(st.session_state.mongodb.find_many(
                st.session_state.login_collection, {}
            ))

        data = st.session_state.data
        login_data = st.session_state.login_data
        df = pd.DataFrame(data)
        login_df = pd.DataFrame(login_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        login_df['timestamp'] = pd.to_datetime(login_df['timestamp'])

        col1, col2, col3, col4, col5 = st.columns(5)

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        df_today = df[df['timestamp'].dt.date == today]
        df_yesterday = df[df['timestamp'].dt.date == yesterday]

        metrics_all = cls.calculate_metrics(df)
        metrics_today = cls.calculate_metrics(df_today)
        metrics_yesterday = cls.calculate_metrics(df_yesterday)

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


        # Thời gian sử dụng
        total_usage_time = df['processing_time'].sum() / 60  # in minutes
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng thời gian xử lý (phút)", f"{total_usage_time:.2f}")

        # Thống kê người dùng
        active_users_today = df_today['username'].nunique()
        active_users_week = df[df['timestamp'] > (datetime.now() - timedelta(days=7))]['username'].nunique()
        avg_question_length = df['input_word_count'].mean()
        avg_answer_length = df['output_word_count'].mean()


        col2.metric("Độ dài TB câu hỏi (từ)", f"{avg_question_length:.2f}")


        col3.metric("Độ dài TB câu trả lời (từ)", f"{avg_answer_length:.2f}")










class TimeProcessVisualize:
    @classmethod
    def show(cls):
        if "data" not in st.session_state:
            st.session_state.data = list(st.session_state.mongodb.find_many(
                st.session_state.chat_collection, {}
            ))

        data = st.session_state.data
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # st.html('<p class="medium-font">Biểu Đồ Thống Kê</p>')

        fig_line = px.line(df, x='timestamp', y='processing_time', title='Thời Gian Xử Lý Theo Thời Gian')
        fig_line.update_layout(xaxis_title="Thời Gian", yaxis_title="Thời Gian Xử Lý (giây)")
        st.plotly_chart(fig_line, use_container_width=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Group the data by date
        df['date'] = df['timestamp'].dt.date
        df_daily = df.groupby('date').agg({
            'processing_time': ['mean', 'max']
        }).reset_index()

        # Rename columns for easier access
        df_daily.columns = ['date', 'avg_processing_time', 'max_processing_time']

        # Create the figure
        fig = go.Figure()

        # Add the bar trace for average processing time
        fig.add_trace(go.Bar(x=df_daily['date'], y=df_daily['avg_processing_time'], name='Trung bình'))

        # Add the line trace for maximum processing time
        fig.add_trace(go.Scatter(x=df_daily['date'], y=df_daily['max_processing_time'], name='Tối đa', mode='lines'))

        # Update the layout
        fig.update_layout(
            title='Thời gian xử lý theo ngày',
            xaxis_title='Ngày',
            yaxis_title='Thời gian (giây)'
        )

        # Display the figure in Streamlit
        st.plotly_chart(fig, use_container_width=True)


class AccountManager:
    @classmethod
    def show(cls):

        if "login_data" not in st.session_state:
            st.session_state.login_data = list(st.session_state.mongodb.find_many(
                st.session_state.login_collection, {}
            ))

        login_data = st.session_state.login_data
        login_df = pd.DataFrame(login_data)
        login_df['timestamp'] = pd.to_datetime(login_df['timestamp'])
        banned_usernames = set(
            doc['username'] for doc in st.session_state.mongodb.find_many(st.session_state.ban_collection, {}))

        total_accounts = len(login_df['username'].unique())
        active_accounts = total_accounts - len(banned_usernames)

        col1, col2, col3 = st.columns(3)
        col1.metric("Tổng số tài khoản", total_accounts)
        col2.metric("Tài khoản đang hoạt động", active_accounts)
        col3.metric("Tài khoản bị chặn", len(banned_usernames))
        # st.html('<p class="medium-font">IP Gửi Nhiều Request Nhất</p>')

        banned_usernames = set(doc['username'] for doc in st.session_state.mongodb.find_many(st.session_state.ban_collection, {}))
        st.markdown('<h4>QUẢN LÝ TÀI KHOẢN</h4>', unsafe_allow_html=True)
        if login_df is not None and not login_df.empty:
            non_banned_usernames = login_df[~login_df['username'].isin(banned_usernames)]['username']
            username_counts = Counter(non_banned_usernames)

            num_usernames = st.selectbox("Chọn số lượng username muốn hiển thị",
                                         options=range(1, min(11, len(username_counts) + 1)),
                                         index=min(4, len(username_counts) - 1))

            top_usernames = username_counts.most_common(num_usernames)

            for username, count in top_usernames:
                col1, col2, col3 = st.columns([2, 1, 1])

                if username == st.session_state.username:
                    col1.markdown(f"<span style='color: #1E90FF;'><strong>Username: {username}</strong></span>",
                                  unsafe_allow_html=True)
                    col2.markdown(f"<span style='color: #1E90FF;'><strong>Số lượng: {count}</strong></span>",
                                  unsafe_allow_html=True)
                elif username in banned_usernames:
                    col1.markdown(f"<span style='color: #DC143C;'>Username: {username}</span>", unsafe_allow_html=True)
                    col2.write(f"Số lượng: {count}")
                else:
                    col1.write(f"Username: {username}")
                    col2.write(f"Số lượng: {count}")

                if username == st.session_state.username:
                    col3.markdown("<span style='color: #1E90FF;'>(Tài khoản của bạn)</span>", unsafe_allow_html=True)
                elif username in banned_usernames:
                    col3.markdown("<span style='color: #DC143C;'>(Đã bị chặn)</span>", unsafe_allow_html=True)
                else:
                    if col3.button("Chặn", key=f"ban_{username}"):
                        st.session_state.mongodb.insert_one(st.session_state.ban_collection,
                                                            {"username": username, "banned_at": datetime.now()})
                        st.success(f"Đã chặn username {username}")
                        st.rerun()
            # username_df = pd.DataFrame(top_usernames, columns=['Username', 'Số lượng truy cập'])
            # fig_username = px.bar(username_df, x='Username', y='Số lượng truy cập',
            #                       title=f'Top {num_usernames} username có nhiều truy cập nhất')
            # st.plotly_chart(fig_username, use_container_width=True)

            st.markdown('<h4>DANH SÁCH CHẶN</h4>', unsafe_allow_html=True)

            banned_usernames_data = list(st.session_state.mongodb.find_many(st.session_state.ban_collection, {}))
            if banned_usernames_data:
                banned_df = pd.DataFrame(banned_usernames_data)
                banned_df['banned_at'] = pd.to_datetime(banned_df['banned_at'])
                banned_df = banned_df.sort_values('banned_at', ascending=False)

                for _, row in banned_df.iterrows():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    col1.write(f"Username: {row['username']}")
                    col2.write(f"Bị cấm lúc: {row['banned_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                    if col3.button(f"Gỡ chặn", key=f"unban_{row['username']}"):
                        st.session_state.mongodb.delete_one(st.session_state.ban_collection, {"username": row['username']})
                        st.success(f"Đã gỡ cấm username {row['username']}")
                        st.experimental_rerun()
            else:
                st.write("Không có username nào bị chặn.")
        else:
            st.write("Không có dữ liệu đăng nhập.")





class SearchMessageManager:
    @classmethod
    def show(cls):
        if "data" not in st.session_state:
            st.session_state.data = list(st.session_state.mongodb.find_many(
                st.session_state.chat_collection, {}
            ))

        data = st.session_state.data
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # st.html('<p class="medium-font">Tìm Kiếm và Lọc</p>')
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("Tìm kiếm")
        with col2:
            date_range = st.date_input("Chọn khoảng thời gian", [datetime.now() - timedelta(days=7), datetime.now()])

        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = df[
                (df['question'].str.contains(search_term, case=False, na=False) | df['answer'].str.contains(search_term, case=False, na=False)) &
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
            'processing_time': 'Thời Gian Xử Lý (giây)',
            'username': 'Người hỏi'
        })

        st.markdown(f"**Kết quả:** `{len(filtered_df)}` bản ghi")
        st.dataframe(
            filtered_df_renamed[
                ['Câu Hỏi', 'Câu Trả Lời', 'Thời Gian', 'Số Từ Input', 'Số Từ Output', 'Thời Gian Xử Lý (giây)', 'Người hỏi']],
            height=300
        )

        # Tokenize text and count word frequencies
        def tokenize(text):
            words = re.findall(r'\w+', text.lower())
            return words

        all_questions = ' '.join(filtered_df['question'].dropna())
        all_answers = ' '.join(filtered_df['answer'].dropna())

        question_words = tokenize(all_questions)
        answer_words = tokenize(all_answers)

        question_word_counts = Counter(question_words)
        answer_word_counts = Counter(answer_words)

        total_question_words = sum(question_word_counts.values())
        total_answer_words = sum(answer_word_counts.values())

        top_question_words = question_word_counts.most_common(10)
        top_answer_words = answer_word_counts.most_common(10)

        question_data = pd.DataFrame(top_question_words, columns=['Từ', 'Số Lần Xuất Hiện'])
        question_data['Tần suất (%)'] = question_data['Số Lần Xuất Hiện'] / total_question_words * 100

        answer_data = pd.DataFrame(top_answer_words, columns=['Từ', 'Số Lần Xuất Hiện'])
        answer_data['Tần suất (%)'] = answer_data['Số Lần Xuất Hiện'] / total_answer_words * 100

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Từ hỏi nhiều nhất")
            st.write(question_data)

        with col2:
            st.markdown("### Từ trả lời nhiều nhất")
            st.write(answer_data)


class SystemInfoManager:
    @classmethod
    def show(cls):
        st.markdown("## Thông Tin Hệ Thống", unsafe_allow_html=True)

        # Thông tin cơ bản
        col1, col2, col3 = st.columns(3)
        col1.info(f"**Vector Store:** Qdrant")
        col2.info(f"**NoSQL Store:** MongoDB")
        col3.info(f"**Chat Model:** {st.session_state.mode_chat}")

        col1, col2 = st.columns(2)
        col1.info(f"**Embedded Model:** {st.session_state.model_embed}")
        col2.info(f"**Current Database:** {st.session_state.current_data}")

        # Thông tin chi tiết
        st.markdown("### Chi tiết cấu hình")

        # Thông tin hệ thống
        system_info = {
            "Hệ điều hành": platform.system(),
            "Phiên bản": platform.version(),
            "Kiến trúc": platform.machine(),
            "Processor": platform.processor(),
            "RAM Total": f"{psutil.virtual_memory().total / (1024 ** 3):.2f} GB",
            "RAM Available": f"{psutil.virtual_memory().available / (1024 ** 3):.2f} GB",
            "Disk Usage": f"{psutil.disk_usage('/').percent}%"
        }

        col1, col2 = st.columns(2)
        for i, (key, value) in enumerate(system_info.items()):
            if i % 2 == 0:
                col1.info(f"**{key}:** {value}")
            else:
                col2.info(f"**{key}:** {value}")

        # Thông tin cấu hình
        st.markdown("### Cấu hình ứng dụng")
        config_info = {
            "MongoDB Database": st.session_state.mongo_database,
            "Chat Collection": st.session_state.chat_collection,
            "Login Collection": st.session_state.login_collection,
            "Ban Collection": st.session_state.ban_collection,
        }

        col1, col2 = st.columns(2)
        for i, (key, value) in enumerate(config_info.items()):
            if i % 2 == 0:
                col1.info(f"**{key}:** {value}")
            else:
                col2.info(f"**{key}:** {value}")

        # Thông tin trạng thái
        st.markdown("### Trạng thái hệ thống")
        status_info = {
            "IP Address": st.session_state.ip,
            "Initialized": "Yes" if st.session_state.initialized else "No",
            "Current Date": datetime.now().strftime("%Y-%m-%d"),
            "Uptime": f"{(time.time() - psutil.boot_time()) / 60:.2f} minutes",
            "CPU Usage": f"{psutil.cpu_percent()}%",
            "Active Users": len(set(
                msg['username'] for msg in st.session_state.mongodb.find_many(st.session_state.chat_collection, {})))
        }

        col1, col2 = st.columns(2)
        for i, (key, value) in enumerate(status_info.items()):
            if i % 2 == 0:
                col1.info(f"**{key}:** {value}")
            else:
                col2.info(f"**{key}:** {value}")



