import streamlit as st

class Home:
    @classmethod
    def __new__(cls):
        pass

    @staticmethod
    def show():
        Home.setup_page()
        Home.header()
        Home.introduction()
        Home.admissions()
        Home.majors()
        Home.contact()
        Home.footer()

    @staticmethod
    def setup_page():
        # st.set_page_config(page_title="IUH - Đại học Công nghiệp TP.HCM", layout="wide")
        st.markdown("""
        <style>
        body { font-family: Arial, sans-serif; }
        .title { font-size: 2.5rem; font-weight: bold;}
        .subtitle { font-size: 1.2rem;}
        h2 { margin-top: 2rem; }
        .icon { vertical-align: middle; margin-right: 10px; }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def header():
        st.markdown('<p class="title">🏫 IUH - Đại học Công nghiệp TP.HCM</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Đổi mới - Sáng tạo - Hội nhập</p>', unsafe_allow_html=True)

    @staticmethod
    def introduction():
        st.markdown('## 📚 Giới thiệu')
        st.write("""
        Trường Đại học Công nghiệp là một trong những cơ sở giáo dục đại học hàng đầu tại Việt Nam
        trong lĩnh vực đào tạo kỹ thuật và công nghệ. Với hơn 50 năm lịch sử phát triển, trường đã
        đào tạo hàng chục ngàn kỹ sư, cử nhân có trình độ chuyên môn cao, đáp ứng nhu cầu nhân lực
        cho sự nghiệp công nghiệp hóa, hiện đại hóa đất nước.
        """)

    @staticmethod
    def admissions():
        st.markdown('## 🎓 Tuyển sinh 2024')
        st.info("Thông tin tuyển sinh sẽ được cập nhật sớm!")

    @staticmethod
    def majors():
        st.markdown('## 🏆 Các ngành đào tạo chính')
        col1, col2, col3 = st.columns(3)
        majors = [
            ["🔧 Kỹ thuật Cơ khí", "💻 Công nghệ Thông tin", "⚡ Điện - Điện tử"],
            ["💼 Quản trị Kinh doanh", "📊 Kế toán - Kiểm toán", "🧪 Công nghệ Hóa học"],
            ["🍽️ Công nghệ Thực phẩm", "🏗️ Kỹ thuật Xây dựng", "🎨 Thiết kế Công nghiệp"]
        ]
        for col, major_list in zip([col1, col2, col3], majors):
            with col:
                for major in major_list:
                    st.markdown(major)

    @staticmethod
    def contact():
        st.markdown('## 📞 Liên hệ')
        st.markdown("""
        - 🏢 Địa chỉ: 12 Nguyễn Văn Bảo, Phường 4, Gò Vấp, Hồ Chí Minh
        - ☎️ Điện thoại: (028) 38940390
        - 📧 Email:
            + Trường ĐH Công nghiệp TP.HCM: dhcn@iuh.edu.vn
            + Phòng Tổ chức - Hành chính: ptchc@iuh.edu.vn
            + Phòng Tài chính - Kế toán: ptckt@iuh.edu.vn
            + Phòng Đào tạo: phongdaotao@iuh.edu.vn
            + Bộ phận Tuyển sinh: tuyensinh@iuh.edu.vn
        - 🌐 Website: www.iuh.edu.vn
        """)

    @staticmethod
    def footer():
        st.markdown("---")
        st.markdown("© 2024 Trường Đại học Công nghiệp TP.HCM. Tất cả quyền được bảo lưu.")

if __name__ == "__main__":
    Home.show()