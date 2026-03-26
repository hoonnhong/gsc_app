"""
db_manager.py - 로컬 SQLite 데이터베이스 연동 모듈
Pandas DataFrame을 사용하여 데이터를 읽고 쓰는 기능을 제공하며,
향후 다른 데이터베이스로의 마이그레이션이 용이하도록 추상화되어 있습니다.
"""

import sqlite3
import pandas as pd
import os
from config import Config

class DBManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH
        # 데이터베이스 파일이 위치할 폴더가 없다면 자동으로 생성합니다.
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def get_df(self, table_name):
        """데이터베이스 테이블의 내용을 판다스 데이터프레임으로 읽어옵니다."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = f"SELECT * FROM {table_name}"
                return pd.read_sql_query(query, conn)
        except Exception as e:
            # 아직 테이블이 만들어지지 않았거나 데이터가 없는 경우 빈 표를 반환합니다.
            print(f"⚠️ '{table_name}' 테이블을 읽을 수 없습니다: {e}")
            return pd.DataFrame()

    def save_df(self, df, table_name, if_exists='replace'):
        """판다스 데이터프레임을 데이터베이스 테이블로 저장합니다."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # if_exists='replace'는 기존 테이블이 있으면 지우고 새로 만든다는 뜻입니다.
                df.to_sql(table_name, conn, if_exists=if_exists, index=False)
                return True
        except Exception as e:
            print(f"❌ '{table_name}' 저장 중 오류가 발생했습니다: {e}")
            return False

    def execute(self, query, params=None):
        """데이터 조회 외에 테이블 생성이나 삭제 등 SQL 명령어를 직접 실행합니다."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ SQL 명령 실행 중 오류 발생: {e}")
            return False

# 어디서든 바로 사용할 수 있도록 데이터베이스 관리자 객체를 미리 하나 만들어둡니다.
db = DBManager()
