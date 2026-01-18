
import streamlit as st
from streamlit_option_menu import option_menu

# 1. 페이지 설정
st.set_page_config(
    page_title="Co-op IMS",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 전역 세션 상태 초기화 (AI 필독: 상태 누락 방지)
if 'auth_status' not in st.session_state:
    st.session_state['auth_status'] = False

def main():
    # --- GNB (상단 메뉴) ---
    with st.container():
        selected = option_menu(
            menu_title=None,
            options=["업무자동화", "조합원관리", "설정"],
            icons=["robot", "people", "gear"],
            default_index=0,
            orientation="horizontal"
        )

    # --- Routing (지연 로딩 적용: 성능 최적화) ---
    if selected == "업무자동화":
        from views_admin import automation
        automation.show()

    elif selected == "조합원관리":
        # 서브 메뉴 (Optional: 조합원 관리 내부에서 탭이나 사이드바 사용 가능)
        from views_admin import member_manage
        member_manage.show()

    elif selected == "설정":
        st.info("🚧 환경 설정 기능 준비 중")

if __name__ == "__main__":
    main()
