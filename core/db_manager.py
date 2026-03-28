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
                return cursor.rowcount  # 영향받은 행의 수 반환
        except Exception as e:
            print(f"❌ SQL 명령 실행 중 오류 발생: {e}")
            return -1

    def insert_row(self, table_name: str, data: dict):
        """딕셔너리 데이터를 받아 특정 테이블에 INSERT 합니다. (속도/메모리 최적화)"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(data.values()))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ {table_name} INSERT 오류: {e}")
            return False

    def update_row(self, table_name: str, data: dict, where_clause: str, where_params: tuple):
        """특정 조건에 맞는 행을 업데이트합니다. (예: where_clause="id=?", where_params=(1,))"""
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        params = tuple(data.values()) + where_params
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ {table_name} UPDATE 오류: {e}")
            return False

    def delete_row(self, table_name: str, where_clause: str, where_params: tuple):
        """특정 조건에 맞는 행을 삭제합니다."""
        query = f"DELETE FROM {table_name} WHERE {where_clause}"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, where_params)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ {table_name} DELETE 오류: {e}")
            return False

    def fetch_all(self, query: str, params: tuple = None):
        """SELECT 쿼리를 실행하고 결과를 딕셔너리 리스트로 반환합니다. (Pandas 대체용)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # 컬럼명으로 접근 가능하게 설정
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ SELECT 쿼리 오류: {e}")
            return []

    def setup_auth_tables(self):
        """인증 및 권한 관리를 위한 테이블을 생성합니다."""
        # 1. 사용자 테이블 (아이디, 이름, 비밀번호, 권한 레벨)
        self.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                user_name TEXT NOT NULL,
                user_pwd TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'staff',
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # 2. 권한 테이블 (사용자별 접근 가능 메뉴 ID)
        self.execute('''
            CREATE TABLE IF NOT EXISTS user_permissions (
                user_id TEXT,
                menu_id TEXT,
                PRIMARY KEY (user_id, menu_id)
            )
        ''')
        
        # 초기 최고관리자 계정 생성 (비밀번호: admin123)
        # 보안을 위해 SHA256 해시값으로 저장합니다.
        admin_id = 'admin'
        admin_pwd_hash = '240be518ebb702c2840e6093850130f1ac9c878d654575824559b350f588aa94'
        self.execute('''
            INSERT OR IGNORE INTO users (user_id, user_name, user_pwd, role)
            VALUES (?, ?, ?, ?)
        ''', (admin_id, '최고관리자', admin_pwd_hash, 'admin'))

# 어디서든 바로 사용할 수 있도록 데이터베이스 관리자 객체를 미리 하나 만들어둡니다.
db = DBManager()
# 앱 시작 시 필요한 인증용 테이블들을 자동으로 준비합니다.
db.setup_auth_tables()
