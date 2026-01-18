import streamlit as st
from services.public_service import submit_application

def show():
    st.title("조합원 가입 신청")
    st.write("가입 신청서를 작성해주세요.")
    
    with st.form("application_form"):
        name = st.text_input("이름")
        phone = st.text_input("휴대폰 번호")
        submitted = st.form_submit_button("신청하기")
        
        if submitted:
            submit_application({"name": name, "phone": phone})
            st.success("신청이 접수되었습니다.")
