# Firestore connection manager
import streamlit as st
# import firebase_admin
# from firebase_admin import credentials, firestore

@st.cache_resource
def get_firestore_client():
    """Firestore 클라이언트 생성 (Singleton)"""
    # TODO: Implement Firestore connection logic using secrets.toml
    # if not firebase_admin._apps:
    #     cred = credentials.Certificate(st.secrets["firebase_key"])
    #     firebase_admin.initialize_app(cred)
    # return firestore.client()
    return None

def get_stats():
    """통계 데이터 조회"""
    # db = get_firestore_client()
    # doc = db.collection('public_stats').document('current').get()
    # return doc.to_dict()
    return {"member_count": 0, "total_capital": 0}
