## 1. 프로젝트 헌장 (Project Charter)

* **프로젝트명:** Co-op IMS (한의원 및 협동조합 통합 업무 시스템)
* **개발/운영:** 사무국장 (1인 개발자 + AI Copilot)
* **시스템 성격:**
  * **Internal:** 민감 데이터(환자/회계) → 로컬 네트워크 내부망 전용 (SQLite)
  * **Public:** 공개 데이터(강좌/공지) → 클라우드 연동 하이브리드 (Firestore)
* **핵심 철학:** "Start Small, Grow Smart" (작동하는 MVP를 먼저 만들고, 나중에 다듬는다.)

---

## 2. 시스템 아키텍처 (System Architecture)

### 2.1 기술 스택 (Tech Stack)

| **구분**      | **기술 / 도구**       | **선정 이유 및 AI 지침**                                                       |
| ------------------- | --------------------------- | ------------------------------------------------------------------------------------ |
| **Lang**      | Python 3.10+                | Type Hinting 활용 및 최신 라이브러리 호환성                                          |
| **Core**      | Streamlit                   | Frontend/Backend 통합, 빠른 프로토타이핑                                             |
| **IDE**       | Antigravity / Cursor        | AI 통합 개발 환경 활용                                                               |
| **UI**        | streamlit-option-menu       | 직관적인 GNB(상단) 메뉴 구현                                                         |
| **DB (내부)** | **SQLite (WAL Mode)** | `sqlite3`표준 라이브러리 사용.**SQL Injection 방지(Parameter Binding) 필수** |
| **DB (외부)** | **Firestore**         | `firebase-admin`사용. 외부 예약/조회용 NoSQL                                       |
| **Model**     | **Pydantic**          | **[추가]**데이터 구조 정의 및 검증. AI가 데이터 스키마를 명확히 이해하도록 도움      |
| **Deploy**    | Docker                      | `python:3.10-slim`기반. 볼륨 마운트로 데이터 영속성 보장                           |

### 2.2 폴더 구조 (Directory Structure)

> **AI 지침:** 뷰(View)와 로직(Service)을 분리하여 코드가 섞이지 않게 하십시오.

**Plaintext**

```
my_work_app/
├── .streamlit/              # [설정]
│   ├── secrets.toml         # [보안] DB 접속 정보, API 키 (Git 제외)
│   └── config.toml          # [테마] UI 색상 및 기본 설정
│
├── data/                    # [데이터] Docker Volume 마운트 지점
│   ├── database.db          # SQLite DB 파일
│   └── files/               # 업로드/생성된 파일 저장소
│
├── docs/                    # [문서]
│   ├── manual.md            # 사용자 매뉴얼
│   └── tech_spec.md         # 기술 명세서 (본 문서)
│
├── modules/                 # [인프라] 기술적인 하부 구조 (DB 연결 등)
│   ├── __init__.py
│   ├── db_connector.py      # SQLite/Firestore 연결 관리자 (Singleton)
│   └── utils.py             # 공통 함수 (날짜 변환, 포맷팅 등)
│
├── services/                # [비즈니스 로직] 순수 파이썬 코드 (UI 없음)
│   ├── __init__.py
│   ├── excel_service.py     # 엑셀 병합/처리 로직
│   └── member_service.py    # 조합원 CRUD 로직
│
├── views/                   # [프론트엔드] 화면 UI (Streamlit 코드)
│   ├── __init__.py
│   ├── automation.py        # [Phase 1] 업무 자동화
│   ├── dashboard.py         # [Phase 3] 대시보드
│   └── members/             # [Phase 2] 조합원 관리 패키지
│       ├── __init__.py
│       ├── member_list.py   # 명부 조회/검색
│       └── member_form.py   # 등록/수정 폼
│
├── main.py                  # [진입점] 앱 실행 및 라우팅
├── requirements.txt         # [의존성] 패키지 목록
└── Dockerfile               # [배포] 이미지 빌드 설정
```

---

## 3. 핵심 구현 코드 가이드 (Standard Code Patterns)

AI가 코드를 작성할 때 '표준'으로 참고할 코드 패턴입니다.

### 3.1 메인 라우터 (main.py) - 동적 메뉴 및 상태 초기화

**Python**

```
# main.py
import streamlit as st
from streamlit_option_menu import option_menu

# 1. 페이지 설정
st.set_page_config(
    page_title="Co-op IMS",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 전역 세션 상태 초기화 (AI 필독: 상태 누락 방지)
if 'auth_status' not in st.session_state:
    st.session_state['auth_status'] = False

def main():
    # --- GNB (상단 메뉴) ---
    with st.container():
        selected = option_menu(
            menu_title=None,
            options=["업무자동화", "조합원관리", "설정"],
            icons=["robot", "people", "gear"],
            default_index=0,
            orientation="horizontal"
        )

    # --- Routing (지연 로딩 적용: 성능 최적화) ---
    if selected == "업무자동화":
        from views import automation
        automation.show()

    elif selected == "조합원관리":
        from views.members import member_list
        member_list.show()

    elif selected == "설정":
        st.info("🚧 환경 설정 기능 준비 중")

if __name__ == "__main__":
    main()
```

### 3.2 DB 연결 및 쿼리 실행 (modules/db_connector.py)

AI에게 "SQLite 연결은 반드시 `run_query` 함수를 통해 안전하게 실행해"라고 지시하기 위한 표준입니다.

**Python**

```
# modules/db_connector.py
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
```

### 3.3 로직과 뷰의 분리 (Example)

* **Logic (`services/excel_service.py`):** 순수 Python 함수. 데이터를 받아 처리하고 결과를 리턴. `st.*` 함수 사용 금지.
* **View (`views/automation.py`):** `st.file_uploader`로 파일을 받고, Service 함수를 호출한 뒤, 결과를 `st.dataframe`으로 표시.
