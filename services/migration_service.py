import pandas as pd
import re
import math
from typing import Optional, Tuple
from modules.db_sqlite import get_connection, run_query

class MigrationService:
    """
    엑셀 데이터를 SQLite로 마이그레이션(변환/저장)하는 비즈니스 로직을 담당합니다.
    """

    TABLE_ACCOUNTING = "accounting_transactions"
    
    @staticmethod
    def _clean_category(text: str) -> str:
        """관/항/목/세목 정제: (03)조합사업비용 -> 조합사업비용"""
        if pd.isna(text):
            return ""
        text = str(text)
        text = re.sub(r'\(\d+\)', '', text)  # (03) 제거
        text = re.sub(r'^\d+\s*', '', text)  # 03 제거
        return text.strip()

    @staticmethod
    def _clean_account(text: str) -> str:
        """계좌명 정제: 04 운영비 -> 운영비"""
        if pd.isna(text):
            return ""
        text = str(text)
        return re.sub(r'^\d+\s*', '', text).strip()

    @classmethod
    def process_accounting_data(cls, uploaded_file) -> Optional[int]:
        """
        회계 엑셀 파일을 처리하여 DB에 저장합니다.
        Returns:
            int: 처리된 행의 수 (성공 시)
            None: 처리 실패 시
        """
        try:
            # 1. 엑셀 읽기
            df = pd.read_excel(uploaded_file, usecols=[0, 1, 2, 3, 4, 6, 7, 8, 9], header=0)
            df.columns = ['type', 'gwan', 'hang', 'mok', 'semok', 'summary', 'amount', 'account_name', 'reg_date']

            # 2. 데이터 정제
            df['amount'] = (
                df['amount'].astype(str)
                .str.replace(',', '')
                .str.replace('nan', '0')
            )
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0).astype(int)
            df['reg_date'] = pd.to_datetime(df['reg_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            for col in ['gwan', 'hang', 'mok', 'semok']:
                df[col] = df[col].apply(cls._clean_category)
                
            df['account_name'] = df['account_name'].apply(cls._clean_account)
            
            # 세목적요 분리
            split_desc = df['summary'].fillna("").astype(str).str.split('-', expand=True)
            for i in range(4):
                col_name = f'detail_{i+1}'
                if i < split_desc.shape[1]:
                    df[col_name] = split_desc[i].str.strip()
                else:
                    df[col_name] = ""

            final_cols = ['type', 'gwan', 'hang', 'mok', 'semok', 
                          'detail_1', 'detail_2', 'detail_3', 'detail_4', 
                          'amount', 'account_name', 'reg_date']
            df_final = df[final_cols]

            # 3. DB 저장 (Transaction: Create if not exists & Append)
            conn = get_connection()
            with conn: 
                # 테이블이 없으면 생성 (IF NOT EXISTS)
                conn.execute(f'''
                    CREATE TABLE IF NOT EXISTS {cls.TABLE_ACCOUNTING} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT, gwan TEXT, hang TEXT, mok TEXT, semok TEXT,
                        detail_1 TEXT, detail_2 TEXT, detail_3 TEXT, detail_4 TEXT,
                        amount INTEGER, account_name TEXT, reg_date TEXT
                    )
                ''')
                
                # 데이터 추가 (Append)
                df_final.to_sql(cls.TABLE_ACCOUNTING, conn, if_exists='append', index=False)
            
            return len(df_final)

        except Exception as e:
            # Service layer should raise or log, letting View handle UI error presentation if possible,
            # but standard pattern in this project seems to allow st.error in modules sometimes?
            # No, 'services/excel_service.py ... st.* 함수 사용 금지' in TECH_SPEC.
            # So I should print to console or re-raise.
            print(f"[MigrationService Error] {e}") 
            raise e

    @classmethod
    def get_accounting_summary(cls) -> int:
        """전체 데이터 건수 조회"""
        df = run_query(f"SELECT COUNT(*) FROM {cls.TABLE_ACCOUNTING}", return_df=True)
        return int(df.iloc[0, 0]) if not df.empty else 0

    @classmethod
    def get_accounting_data(cls, limit: int = 20, offset: int = 0) -> pd.DataFrame:
        """데이터 페이징 조회"""
        query = f"SELECT * FROM {cls.TABLE_ACCOUNTING} LIMIT ? OFFSET ?"
        return run_query(query, params=(limit, offset), return_df=True)

    @classmethod
    def get_duplicates(cls) -> pd.DataFrame:
        """
        중복 의심 데이터 조회
        (등기일, 목, 세목, 상세내역, 금액)이 모두 동일한 건들을 조회합니다.
        NULL 값이나 공백 차이로 인한 미검출을 방지하기 위해 COALESCE와 TRIM을 사용합니다.
        """
        # 상세내역 4개 중 하나라도 다르면 중복이 아님? -> 예민하게 설정.
        # SQLite에서 GROUP BY시 NULL은 NULL끼리 그룹핑됨. 따라서 별도 COALESCE 안해도 되지만, 
        # Python에서 None으로 들어간 것과 ""로 들어간 것이 다를 수 있음.
        # process_accounting_data에서 fillna("")를 했으므로 DB엔 ""가 들어감.
        
        query = f"""
            SELECT * FROM {cls.TABLE_ACCOUNTING}
            WHERE (
                reg_date, 
                type,
                mok, 
                semok, 
                COALESCE(detail_1, ''), 
                COALESCE(detail_2, ''), 
                COALESCE(detail_3, ''), 
                COALESCE(detail_4, ''), 
                amount
            ) IN (
                SELECT 
                    reg_date, 
                    type,
                    mok, 
                    semok, 
                    COALESCE(detail_1, ''), 
                    COALESCE(detail_2, ''), 
                    COALESCE(detail_3, ''), 
                    COALESCE(detail_4, ''), 
                    amount
                FROM {cls.TABLE_ACCOUNTING}
                GROUP BY 
                    reg_date, 
                    type,
                    mok, 
                    semok, 
                    COALESCE(detail_1, ''), 
                    COALESCE(detail_2, ''), 
                    COALESCE(detail_3, ''), 
                    COALESCE(detail_4, ''), 
                    amount
                HAVING COUNT(*) > 1
            )
            ORDER BY reg_date ASC, mok ASC
        """
        return run_query(query, return_df=True)

    @classmethod
    def update_transaction(cls, id: int, data: dict):
        """데이터 수정"""
        # data 딕셔너리의 키를 이용하여 동적 쿼리 생성
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = list(data.values())
        values.append(id)
        
        query = f"UPDATE {cls.TABLE_ACCOUNTING} SET {set_clause} WHERE id = ?"
        run_query(query, params=tuple(values))

    @classmethod
    def delete_transaction(cls, id: int):
        """데이터 삭제"""
        query = f"DELETE FROM {cls.TABLE_ACCOUNTING} WHERE id = ?"
        run_query(query, params=(id,))

    @classmethod
    def delete_all_transactions(cls):
        """전체 데이터 삭제"""
        query = f"DELETE FROM {cls.TABLE_ACCOUNTING}"
        run_query(query)

