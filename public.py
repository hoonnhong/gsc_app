import streamlit as st
from streamlit_option_menu import option_menu

# 1. 페이지 설정
st.set_page_config(
    page_title="Co-op Public",
    layout="wide",
)

def main():
    # --- GNB (상단 메뉴) ---
    with st.container():
        selected = option_menu(
            menu_title=None,
            options=["가입신청", "결과조회", "조합현황"],
            icons=["pencil", "search", "bar-chart"],
            default_index=0,
            orientation="horizontal"
        )

    # --- Routing ---
    if selected == "가입신청":
        from views_public import apply_form
        apply_form.show()

    elif selected == "결과조회":
        from views_public import check_status
        check_status.show()

    elif selected == "조합현황":
        from views_public import stats_viewer
        stats_viewer.show()

if __name__ == "__main__":
    main()
