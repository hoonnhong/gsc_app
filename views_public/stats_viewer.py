import streamlit as st
from services.public_service import get_public_dashboard_stats

def show():
    st.title("조합 현황")
    stats = get_public_dashboard_stats()
    
    col1, col2 = st.columns(2)
    col1.metric("조합원 수", f"{stats['member_count']}명")
    col2.metric("총 출자금", f"{stats['total_capital']:,}원")
