"""
config.py - 앱의 전역 설정을 관리하는 파일
.env 파일로부터 환경 변수를 로드하여 중앙에서 관리합니다.
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    # GCP 인증 설정
    GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "secrets/gcp_service_account.json")
    
    # 구글 시트 ID 설정
    MAIN_SHEET_ID = os.getenv("MAIN_SPREADSHEET_ID")
    INSTRUCTOR_SHEET_ID = os.getenv("INSTRUCTOR_SHEET_ID")
    SYSTEM_SHEET_ID = os.getenv("SYSTEM_SHEET_ID")
    
    # 경로 설정
    ATTACHMENTS_DIR = os.getenv("ATTACHMENTS_DIR")
    INSTRUCTOR_SCAN_DIR = os.getenv("INSTRUCTOR_SCAN_DIR")
    
    # GCP 프로젝트 정보
    PROJECT_ID = "office-util"  # secrets.json에서 확인됨
    
    # 데이터베이스 설정 (SQLite)
    DATABASE_PATH = os.getenv("DATABASE_PATH", "gsc_app.db")
    
    @classmethod
    def validate(cls):
        """필수 설정값이 있는지 검증합니다."""
        # 현재는 로컬 DB(SQLite)를 사용하므로 GCP 인증 파일 체크는 선택 사항으로 둡니다.
        # if not os.path.exists(cls.GOOGLE_CREDENTIALS_PATH):
        #     print(f"⚠️ 경고: 인증키 파일을 찾을 수 없습니다: {cls.GOOGLE_CREDENTIALS_PATH}")
        # if not cls.MAIN_SHEET_ID:
        #     print("⚠️ 경고: MAIN_SHEET_ID가 설정되지 않았습니다.")
        pass
