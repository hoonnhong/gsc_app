import streamlit as st

def show():
    st.title("업무 자동화")
    st.write("엑셀 파일 업로드 및 자동화 기능을 제공합니다.")
    
    uploaded_file = st.file_uploader("엑셀 파일 업로드", type=['xlsx', 'xls'])
    if uploaded_file:
        st.success("파일이 업로드되었습니다.")
        # 추후 excel_service 연동
