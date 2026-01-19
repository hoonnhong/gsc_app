import pandas as pd
import sqlite3
import re
from typing import List, Optional, Tuple
from modules.db_sqlite import get_connection, run_query

class AccountingService:
    """
    회계 장부 데이터 조회 및 분석을 위한 서비스
    """
    TABLE_NAME = "accounting_transactions"

    @classmethod
    def get_distinct_values(cls, column: str, filters: dict = {}, search_keyword: str = "") -> List[str]:
        """
        특정 컬럼의 중복되지 않은 값(Distinct) 목록을 조회합니다.
        
        Args:
            column: 조회할 컬럼명
            filters: 다른 컬럼들의 필터 조건 (cascade filtering)
            search_keyword: 통합 검색 키워드 (세목, 상세1~4 컬럼 대상)
        """
        valid_columns = [
            'type', 'gwan', 'hang', 'mok', 'semok', 
            'detail_1', 'detail_2', 'detail_3', 'detail_4',
            'account_name'
        ]
        if column not in valid_columns:
            return []
            
        sql = f"SELECT DISTINCT {column} FROM {cls.TABLE_NAME}"
        conditions = [f"{column} IS NOT NULL", f"{column} != ''"]
        params = []

        # Cascade Filters 적용
        if filters:
            for col, values in filters.items():
                if col == column or not values:
                    continue # 자기 자신에 대한 필터는 제외
                
                placeholders = ", ".join(["?"] * len(values))
                conditions.append(f"{col} IN ({placeholders})")
                params.extend(values)
                
        # Keyword Search 적용 (Cascade)
        if search_keyword:
            keyword_pattern = f"%{search_keyword}%"
            search_cols = ['semok', 'detail_1', 'detail_2', 'detail_3', 'detail_4']
            
            # OR 조건 생성: (col1 LIKE ? OR col2 LIKE ? ...)
            or_conditions = [f"{col} LIKE ?" for col in search_cols]
            keyword_condition = f"({' OR '.join(or_conditions)})"
            
            conditions.append(keyword_condition)
            params.extend([keyword_pattern] * len(search_cols))
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
            
        sql += f" ORDER BY {column}"
        
        df = run_query(sql, params=tuple(params), return_df=True)
        return df[column].tolist() if not df.empty else []

    @classmethod
    def search_transactions(cls, columns: List[str] = [], where_clause: str = "", filters: dict = {}, search_keyword: str = "", start_date: str = None, end_date: str = None, exclude_filters: dict = {}) -> pd.DataFrame:
        """
        동적 쿼리를 생성하여 회계 데이터를 조회합니다.
        
        Args:
            columns (List[str]): 조회할 컬럼 리스트 (빈 리스트인 경우 전체 컬럼 *)
            where_clause (str): SQL WHERE 절 (사용자 입력)
            columns (List[str]): 조회할 컬럼 리스트 (빈 리스트인 경우 전체 컬럼 *)
            where_clause (str): SQL WHERE 절 (사용자 입력)
            where_clause (str): SQL WHERE 절 (사용자 입력)
            filters (dict): 컬럼별 필터 조건 (예: {'type': ['수입'], 'gwan': ['운영비', '사업비']})
            search_keyword (str): 통합 검색 키워드 (세목, 상세1~4 컬럼 대상 LIKE 검색)
            start_date (str): 검색 시작일 (YYYY-MM-DD)
            end_date (str): 검색 종료일 (YYYY-MM-DD)
            exclude_filters (dict): 제외할 필터 조건 (예: {'gwan': ['선급금']}) -> NOT IN (...)
        """
        # 1. 컬럼 선택
        if not columns:
            select_cols = "*"
        else:
            # SQL Injection 방지는 라이브러리 레벨에서 한계가 있으므로, 
            # 허용된 컬럼명인지 검증하거나 따옴표로 감싸는 것이 좋음.
            # 여기서는 내부 관리자용이므로 유연성을 위해 단순 결합하되, 기본적 검증만 수행.
            valid_columns = [
                'id', 'type', 'gwan', 'hang', 'mok', 'semok', 
                'detail_1', 'detail_2', 'detail_3', 'detail_4', 
                'amount', 'account_name', 'reg_date'
            ]
            safe_cols = [c for c in columns if c in valid_columns]
            if not safe_cols:
                select_cols = "*"
            else:
                select_cols = ", ".join(safe_cols)

        # 2. WHERE 절 구성
        # 기본적인 SQL Injection 키워드 정도만 필터링 (선택 사항)
        clean_where = where_clause.strip()
        
        # WHERE 절이 있으면 "WHERE" 키워드 자동 추가 여부 결정
        sql = f"SELECT {select_cols} FROM {cls.TABLE_NAME}"
        
        if clean_where:
            # "WHERE"로 시작하지 않으면 붙여줌
            if not re.match(r'(?i)^where', clean_where):
                base_where_sql = f"WHERE {clean_where}"
            else:
                base_where_sql = f" {clean_where}"
        else:
            base_where_sql = ""
            
        # 3. List Filter 처리
        # filters = {'type': ['수입'], 'gwan': ['운영비', '사업비']}
        filter_conditions = []
        params = []
        
        for col, values in filters.items():
            if not values:
                continue
            # values 리스트를 SQL IN 절로 변환
            # 예: gwan IN (?, ?)
            placeholders = ", ".join(["?"] * len(values))
            condition = f"{col} IN ({placeholders})"
            filter_conditions.append(condition)
            params.extend(values)

        # 3-2. Exclude Filter 처리 (NOT IN) - [NEW]
        for col, values in exclude_filters.items():
            if not values:
                continue
            placeholders = ", ".join(["?"] * len(values))
            condition = f"{col} NOT IN ({placeholders})"
            filter_conditions.append(condition)
            params.extend(values)

        # 4. Keyword Search 처리 (semok, detail_1 ~ 4)
        if search_keyword:
            keyword_pattern = f"%{search_keyword}%"
            # 검색 대상 컬럼
            search_cols = ['semok', 'detail_1', 'detail_2', 'detail_3', 'detail_4']
            
            # OR 조건 생성: (col1 LIKE ? OR col2 LIKE ? ...)
            or_conditions = [f"{col} LIKE ?" for col in search_cols]
            keyword_condition = f"({' OR '.join(or_conditions)})"
            
            filter_conditions.append(keyword_condition)
            # 파라미터 추가 (컬럼 개수만큼 반복)
            params.extend([keyword_pattern] * len(search_cols))

        # 5. Date Range 필터
        if start_date:
            filter_conditions.append("reg_date >= ?")
            params.append(start_date)
        if end_date:
            filter_conditions.append("reg_date <= ?")
            params.append(end_date)
            
        # WHERE 절 결합
        final_where_clauses = []
        
        # 3-1. 사용자 입력 raw WHERE 절 (있으면)
        if base_where_sql:
            # "WHERE " 제거 후 괄호로 감싸서 안전하게 결합?
            # 기존 base_where_sql은 "WHERE condition" 형태
            raw_cond = re.sub(r'(?i)^where\s+', '', base_where_sql)
            final_where_clauses.append(f"({raw_cond})")
            
        # 3-2. 필터 조건 (있으면)
        if filter_conditions:
            final_where_clauses.append(" AND ".join(filter_conditions))
            
        # 최종 SQL 조립
        if final_where_clauses:
            sql += " WHERE " + " AND ".join(final_where_clauses)
            
        # 4. 정렬
        # 정렬 기본값 (등기일 내림차순)
        # 사용자가 ORDER BY를 직접 썼을 수도 있으니 체크 (where_clause에 포함될 수도 있음 - 드물지만)
        if "order by" not in clean_where.lower():
            sql += " ORDER BY reg_date DESC, id DESC"
            
        try:
            return run_query(sql, params=tuple(params), return_df=True)
        except Exception as e:
            # 쿼리 오류 시 빈 데이터프레임 대신 에러 메시지를 담은 DataFrame 반환하거나 throw
            # 여기서는 호출측에서 처리하도록 throw
            raise ValueError(f"쿼리 실행 오류: {e}")

    @staticmethod
    def calculate_totals(df: pd.DataFrame) -> Tuple[int, int, int]:
        """
        조회된 데이터프레임에서 수입/지출 합계 및 잔액을 계산합니다.
        Args:
            df: 조회된 데이터프레임
        Returns:
            (total_income, total_expense, balance)
        """
        if df.empty or 'amount' not in df.columns or 'type' not in df.columns:
            return 0, 0, 0
            
        # 수입/지출 구분 (type 컬럼 값에 따라)
        # 가정: type 컬럼에 '수입', '지출' 텍스트가 포함되어 있다고 전제
        # 실제 데이터: "01 수입", "02 지출" 형태일 수 있음. 포함 여부로 판단.
        
        income_mask = df['type'].astype(str).str.contains("수입", na=False)
        expense_mask = df['type'].astype(str).str.contains("지출", na=False)
        
        total_income = df.loc[income_mask, 'amount'].sum()
        total_expense = df.loc[expense_mask, 'amount'].sum()
        balance = total_income - total_expense
        
        return int(total_income), int(total_expense), int(balance)
