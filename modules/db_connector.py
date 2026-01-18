import sqlite3
import os
import streamlit as st
import pandas as pd

DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "database.db")

@st.cache_resource
def get_connection():
    """SQLite 연결 객체 생성 (Singleton & WAL Mode)"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
      
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")  # 동시성 향상
    return conn

def run_query(query: str, params: tuple = (), return_df: bool = False):
    """
    [Standard] 쿼리 실행 헬퍼 함수
    Args:
        return_df (bool): True면 Pandas DataFrame 반환, False면 cursor 반환(또는 commit)
    """
    conn = get_connection()
    try:
        if return_df:
            # SELECT 조회용 (Pandas)
            return pd.read_sql(query, conn, params=params)
        else:
            # INSERT/UPDATE/DELETE 용
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            return cur.lastrowid
    except Exception as e:
        st.error(f"데이터베이스 오류: {e}")
        return None
