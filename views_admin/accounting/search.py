import streamlit as st
import pandas as pd
from services.accounting_service import AccountingService

# 컬럼 매핑 정보 (English -> Korean)
COLUMN_MAP = {
    'type': '수입/지출',
    'gwan': '관',
    'hang': '항',
    'mok': '목',
    'semok': '세목',
    'detail_1': '상세1',
    'detail_2': '상세2',
    'detail_3': '상세3',
    'detail_4': '상세4',
    'amount': '금액',
    'account_name': '계좌명',
    'reg_date': '등기일'
}

# 역매핑 (Korean -> English)
REVERSE_COLUMN_MAP = {v: k for k, v in COLUMN_MAP.items()}

def translate_korean_columns(where_clause: str) -> str:
    """
    사용자가 입력한 SQL WHERE 절에서 한글 컬럼명을 영문 컬럼명으로 변환합니다.
    단순 문자열 치환을 사용하되, 따옴표('') 안의 값은 치환하지 않도록 주의합니다.
    """
    if not where_clause:
        return ""
        
    # SQL 문자열 파싱 (따옴표로 분리)
    # 짝수 인덱스는 SQL 코드, 홀수 인덱스는 문자열 리터럴('값')
    parts = where_clause.split("'")
    
    # 치환할 키워드 (길이 긴 순서대로 정렬하여 부분 매칭 방지)
    # 예: '세목'이 '목'보다 먼저 치환되어야 함
    keywords = sorted(REVERSE_COLUMN_MAP.keys(), key=len, reverse=True)
    
    translated_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # SQL 코드 부분: 한글 컬럼명 치환
            temp_part = part
            for kr_col in keywords:
                en_col = REVERSE_COLUMN_MAP[kr_col]
                # 단순 치환 (공백 등을 고려하지 않은 단순 매칭)
                # 더 정교한 SQL 파싱이 필요할 수 있으나, 현재 수준에서는 이정도로 충분
                temp_part = temp_part.replace(kr_col, en_col)
            translated_parts.append(temp_part)
        else:
            # 문자열 리터럴 부분: 그대로 유지
            translated_parts.append(f"'{part}'")
            
    return "".join(translated_parts)

def show():
    st.title("📑 회계데이터")

    # --- Sidebar: 검색 조건 ---
    # --- Sidebar: 설정 및 고급 검색 ---
    with st.sidebar:
        st.header("⚙️ 검색 설정")
        
        # 1. 컬럼 선택 (View 설정이므로 사이드바 유지)
        st.markdown("### 1. 컬럼 표기 설정")
        all_columns_kr = list(COLUMN_MAP.values())
        
        # [NEW] 컬럼 선택 모드전환 (포함 vs 제외)
        # 기본적으로 대부분의 컬럼을 보고 싶어하므로 '제외' 모드가 태그가 적게 생겨서 더 깔끔함.
        col_exclude_mode = st.checkbox("제외할 컬럼 선택하기 (체크 시 선택한 컬럼이 숨겨짐)", value=True)
        
        if col_exclude_mode:
            # 제외 모드: 기본적으로 숨길 컬럼만 선택 (예: id, reg_date 등 굳이 안봐도 되는것들?)
            # 여기서는 '계좌명' 등 일부만 숨기고 싶을 때 유용.
            # 초기값: 사용자 입장에서 '전체 다 보고싶다'면 빈 리스트.
            # 기존 default 로직과 맞추려니 복잡하므로, 심플하게 '빈 값' = '전체 보기'로 유도.
            hidden_columns_kr = st.multiselect(
                "숨길 컬럼 선택:",
                all_columns_kr,
                default=[], # 기본은 아무것도 안 숨김 (전체 표시)
                placeholder="숨기고 싶은 컬럼을 선택하세요"
            )
            # 전체에서 숨길 컬럼 뺀 것이 선택된 컬럼
            selected_columns_kr = [c for c in all_columns_kr if c not in hidden_columns_kr]
        else:
            # 포함 모드 (기존 방식)
            default_columns_kr = ['수입/지출', '세목', '상세1', '금액', '등기일', '계좌명']
            selected_columns_kr = st.multiselect(
                "표시할 컬럼 선택:",
                all_columns_kr,
                default=default_columns_kr
            )
        
        selected_columns_en = [REVERSE_COLUMN_MAP[col] for col in selected_columns_kr]
        
        st.divider()
        
        # 2. 상세 조건 (SQL) - 고급 기능이므로 사이드바 유지
        st.markdown("### 2. 고급 조건 (SQL)")
        st.caption("예: `금액 >= 50000 AND 관 = '운영비'`")
        
        with st.expander("참고: 한글 컬럼명 매핑표"):
            st.code("\n".join([f"{k} -> {v}" for k, v in REVERSE_COLUMN_MAP.items()]), language="text")
        
        where_clause = st.text_area(
            "SQL WHERE 절 입력:",
            height=100,
            placeholder="예: 금액 >= 100000 AND 관 = '운영비'"
        )
        
        with st.expander("💡 SQL 작성 도움말 (클릭)"):
            st.markdown("""
            **기본 연산자**
            - `>` (크다), `<` (작다), `>=` (크거나 같다), `=` (같다), `!=` (다르다)
            - `AND` (이고), `OR` (이거나), `NOT` (아님)

            **텍스트 검색 패턴 (LIKE)**
            - **포함**: `상세1 LIKE '%식대%'` ("식대"가 들어간 모든 것)
            - **시작**: `계좌명 LIKE '농협%'` ("농협"으로 시작하는 것)
            - **끝**: `항 LIKE '%비'` ("비"로 끝나는 것)
            
            **목록 포함 여부 (IN)**
            - `관 IN ('운영비', '사업비')`
            - `관 NOT IN ('선급금')`
            
            **팁**: 
            - 한글 컬럼명(`금액`, `관`)을 그대로 쓰시면 됩니다.
            - 문자는 반드시 **작은 따옴표(' ')** 로 감싸주세요.
            """)

    # --- Main Area: 일반 검색 ---
    
    # 1. 통합 검색 (가장 자주 사용)
    st.markdown("### 🔍 통합 검색")
    
    col_search_1, col_search_2 = st.columns([1, 1])
    
    with col_search_1:
        search_keyword = st.text_input(
            "검색어 입력 (내용 전체 검색):",
            placeholder="예: 황재홍, 식대, 이마트...",
            label_visibility="collapsed"
        )
        
    with col_search_2:
        # [Fix] 범위 선택 위젯(st.date_input with range)이 입력 시 오동작하는 문제 해결을 위해
        # 시작일/종료일 위젯을 분리함.
        sub_col_1, sub_col_2 = st.columns(2)
        with sub_col_1:
            start_date_input = st.date_input(
                "시작일",
                value=None,
                label_visibility="collapsed",
                key="search_start_date"
            )
        with sub_col_2:
            end_date_input = st.date_input(
                "종료일",
                value=None,
                label_visibility="collapsed",
                key="search_end_date"
            )
        
    start_date = start_date_input.strftime("%Y-%m-%d") if start_date_input else None
    end_date = end_date_input.strftime("%Y-%m-%d") if end_date_input else None

    # 2. 상세 필터 (Excel 스타일)
    filters = {}
    exclude_filters = {}
    filter_cols = ['type', 'account_name', 'gwan', 'hang', 'mok', 'semok', 'detail_1', 'detail_2']
    
    # [Start] 기본 필터 설정 로직
    # '관' 컬럼에서 특정 항목(선급금 등)은 기본적으로 제외되도록 설정
    # 방식 변경: '제외 모드'를 활성화하고, 해당 키워드를 선택된 상태로 둠.
    if 'filter_gwan' not in st.session_state and 'exclude_mode_gwan' not in st.session_state:
        try:
            excluded_keywords = ['선급금', '예수금', '이월금', '임시계정', '제예금']
            st.session_state['filter_gwan'] = excluded_keywords
            st.session_state['exclude_mode_gwan'] = True # 제외 모드 활성화
        except Exception as e:
            print(f"Error initializing default filters: {e}")
    # [End] 기본 필터 설정 로직
    
    # 공간 절약을 위해 접이식으로 배치, 기본적으로는 열려있게 함 (자주 쓰니까)
    with st.expander("🎨 상세 필터 (클릭하여 펼치기/접기)", expanded=True):
        st.caption("항목을 선택하여 포함하거나 제외할 수 있습니다.")
        
        # 현재 선택된 필터 상태 파악 (Cascade)
        current_state = {}
        for col in filter_cols:
            key = f"filter_{col}"
            if key in st.session_state:
                current_state[col] = st.session_state[key]
        
        # 3단 컬럼 레이아웃 적용
        cols = st.columns(3)
        
        for i, col_en in enumerate(filter_cols):
            col_kr = COLUMN_MAP.get(col_en, col_en)
            try:
                # Context Filter 생성
                context_filters = {k: v for k, v in current_state.items() if k != col_en and v}
                
                # Distinct 값 조회
                options = AccountingService.get_distinct_values(col_en, filters=context_filters, search_keyword=search_keyword)
                
                if options:
                    with cols[i % 3]:
                        # 현재 선택된 개수 파악 (라벨용)
                        selected_count = 0
                        is_exclude_active = False
                        
                        # session_state에서 직접 상태 확인 (아직 위젯이 렌더링 안됐을 수도 있으나, 값은 있을 수 있음)
                        filter_key = f"filter_{col_en}"
                        exclude_key = f"exclude_mode_{col_en}"
                        
                        if filter_key in st.session_state:
                            selected_count = len(st.session_state[filter_key])
                        if exclude_key in st.session_state:
                            is_exclude_active = st.session_state[exclude_key]
                            
                        # 버튼 라벨 동적 생성
                        if selected_count == 0:
                            label = f"{col_kr}"
                        else:
                            status = "제외" if is_exclude_active else "선택"
                            label = f"{col_kr} ({selected_count} {status})"
                            
                        # Popover (드롭다운) 생성
                        with st.popover(label, use_container_width=True):
                            st.caption(f"{col_kr} 필터 설정")
                            
                            # 1. 제외 모드 체크박스 (Popover 내부로 이동)
                            is_exclude = st.checkbox(
                                "선택 항목 제외하기 (Exclude)", 
                                key=exclude_key,
                                help=f"켜면 선택된 항목을 제외하고 검색합니다."
                            )
                            
                            # 2. Multiselect
                            multiselect_kwargs = {
                                "label": f"{col_kr} 항목 선택", # Popover 안이라 심플하게
                                "options": options,
                                "key": filter_key,
                                "placeholder": "전체(필터 없음)"
                            }
                            # Default 값 설정 (최초 로딩 시)
                            if filter_key not in st.session_state:
                                multiselect_kwargs["default"] = []

                            selected_opts = st.multiselect(**multiselect_kwargs)
                            
                            # 필터 적용
                            if selected_opts:
                                if is_exclude:
                                    exclude_filters[col_en] = selected_opts
                                else:
                                    filters[col_en] = selected_opts
                                
            except Exception as e:
                print(f"Error loading filter for {col_en}: {e}")

    # 검색 버튼 (메인 영역)
    col_btn_1, col_btn_2 = st.columns([8, 2])
    with col_btn_2:
        search_pressed = st.button("검색 결과 업데이트 🔄", type="primary", use_container_width=True)

    # --- Main: 결과 표시 ---
    
    # 쿼리 실행
    try:
        # 계산을 위해 type, amount는 필수
        fetch_columns = list(set(selected_columns_en + ['type', 'amount']))
        
        # 한글 컬럼명 변환
        translated_where = translate_korean_columns(where_clause)
        if translated_where != where_clause:
            pass

        df = AccountingService.search_transactions(
            fetch_columns, 
            translated_where, 
            filters=filters, 
            search_keyword=search_keyword,
            start_date=start_date,
            end_date=end_date,
            exclude_filters=exclude_filters
        )
        
        # --- 요약 정보 (Totals) ---
        total_income, total_expense, balance = AccountingService.calculate_totals(df)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("수입 합계", f"{total_income:,}원")
        col2.metric("지출 합계", f"{total_expense:,}원")
        col3.metric("잔액 (수입-지출)", f"{balance:,}원")
        
        st.divider()
        
        # --- 데이터 테이블 ---
        st.markdown(f"**총 {len(df)}건 검색됨**")
        
        # --- Pagination Logic ---
        col_page_1, col_page_2 = st.columns([8, 2])
        with col_page_2:
            page_size = st.selectbox("페이지 당 개수", [10, 20, 50, 100], index=1, key="accounting_page_size")
        
        # Initialize page state
        if 'accounting_page_num' not in st.session_state:
            st.session_state['accounting_page_num'] = 1
            
        # 검색 실행 시 페이지 초기화 확인 (st.button으로 검색했으므로 여기선 로직 생략, 필요 시 콜백 사용)
        # 하지만 사용자가 검색 조건을 바꾸면 보통 1페이지로 가는게 맞음. 
        # 간단히: 데이터프레임 길이가 바뀌면(새 검색) 리셋하는 로직을 추가하거나, 검색 버튼에 reset 로직을 넣어야 함.
        # 여기서는 검색 버튼 클릭 시 리셋하도록 메인 루프에서 처리하는게 좋지만, 일단 현재 상태 유지.
        
        total_rows = len(df)
        total_pages = (total_rows - 1) // page_size + 1
        
        # 현재 페이지 유효성 검사
        if st.session_state['accounting_page_num'] > total_pages:
            st.session_state['accounting_page_num'] = max(1, total_pages)
            
        current_page = st.session_state['accounting_page_num']
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)
        
        # Slice DataFrame
        df_sliced = df.iloc[start_idx:end_idx]
        
        # 화면에 표시할 때는 사용자가 선택한 컬럼만 (영문 기준 필터링)
        display_cols_en = [c for c in selected_columns_en if c in df_sliced.columns]
        
        # 데이터프레임 컬럼명을 한국어로 변환하여 표시
        df_display = df_sliced[display_cols_en].rename(columns=COLUMN_MAP)
        
        # [Fix] 금액 컬럼 숫자형 변환 (혹시 모를 문자열 혼입 방지 및 포맷팅 준비)
        if "금액" in df_display.columns:
            df_display["금액"] = pd.to_numeric(df_display["금액"], errors='coerce').fillna(0)

        # [Style] 금액에 천단위 콤마 적용 (Pandas Styler 사용)
        styler = df_display.style.format({
            "금액": "{:,.0f}" 
        })

        column_config = {
            "등기일": st.column_config.DateColumn(format="YYYY-MM-DD"),
        }
        
        st.dataframe(
            styler,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
            height=(len(df_display) + 1) * 35 + 3  # [Fix] 행 개수에 따른 동적 높이 조절 (헤더 + 행)
        )
        
        # --- Pagination Controls ---
        st.divider()
        
        # [Style] 버튼의 외곽선을 없애고 텍스트 링크처럼 보이게 하는 CSST
        st.markdown("""
        <style>
        div[data-testid="column"] button[kind="secondary"] {
            border: none;
            background: transparent;
            box-shadow: none; 
            padding: 0px 10px;
            color: #555;
        }
        div[data-testid="column"] button[kind="secondary"]:hover {
            color: #000;
            background: #f0f2f6;
            font-weight: bold;
        }
        div[data-testid="column"] button[kind="secondary"]:disabled {
            color: #ccc;
            background: transparent;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # [Fix] 버튼 정렬 및 찌그러짐 방지를 위한 컬럼 비율 조정 (양옆 여백을 줘서 중앙 정렬)
        _, col_p1, col_p2, col_p3, col_p4, col_p5, _ = st.columns([14, 2, 2, 3, 2, 2, 14])
        
        def set_page(p):
            st.session_state['accounting_page_num'] = p

        with col_p1:
            if st.button("처음", disabled=(current_page == 1), key="btn_first"):
                set_page(1)
                st.rerun()
        with col_p2:
            if st.button("< 이전", disabled=(current_page == 1), key="btn_prev"):
                set_page(current_page - 1)
                st.rerun()
        with col_p3:
            st.markdown(f"<div style='text-align: center; line-height: 38px; font-weight: bold; color: #333;'>{current_page} / {total_pages}</div>", unsafe_allow_html=True)
        with col_p4:
            if st.button("다음 >", disabled=(current_page == total_pages), key="btn_next"):
                set_page(current_page + 1)
                st.rerun()
        with col_p5:
            if st.button("마지막", disabled=(current_page == total_pages), key="btn_last"):
                set_page(total_pages)
                st.rerun()
        
    except Exception as e:
        st.error(f"검색 중 오류가 발생했습니다: {e}")
        st.warning("SQL 구문 오류 가능성이 높습니다. (컬럼명 오타 등)")
