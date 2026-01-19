import streamlit as st
from . import search, dashboard

def show():
    # --- Sidebar: Accounting Navigation (LNB) ---
    with st.sidebar:
        # [Design] 상단 고정 영역: 서브 메뉴
        st.subheader("회계관리 메뉴")
        
        # 라디오 버튼으로 페이지 전환 (가시성 확보를 위해 label_visibility는 유지하거나 커스텀)
        menu = st.radio(
            "이동",
            ["회계데이터", "통계 대시보드", "설정"],
            label_visibility="collapsed",
            key="accounting_lnb"
        )
        
        st.divider() # 상단 네비게이션과 하단 필터 영역 분리
        
    # --- Main Content Routing ---
    if menu == "회계데이터":
        # 기존 회계 장부 검색 페이지
        search.show()
        
    elif menu == "통계 대시보드":
        # 신규 대시보드 페이지 (Placeholder)
        dashboard.show()
        
    elif menu == "설정":
        st.title("⚙️ 회계 설정")
        st.info("🚧 예산 관리 및 마감 설정 기능 준비 중입니다.")
