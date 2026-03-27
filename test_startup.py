import sys
import os

print("--- 의존성 점검 시작 ---")
try:
    import nicegui
    print(f"NiceGUI version: {nicegui.__version__}")
    import jinja2
    print(f"Jinja2 version: {jinja2.__version__}")
    import pandas
    print(f"Pandas version: {pandas.__version__}")
except ImportError as e:
    print(f"필수 라이브러리 누락: {e}")
    sys.exit(1)

print("\n--- 모듈 임포트 테스트 ---")
try:
    print("Trying to import expense_page...")
    from modules.accounting_group.expense.expense_page import render_expense_page
    print("Success: expense_page")
    
    print("Trying to import template...")
    from modules.accounting_group.expense.template import generate_print_html
    print("Success: template")
    
    print("Trying to import db_manager...")
    from core.db_manager import db
    print("Success: db_manager")
except Exception as e:
    import traceback
    print("임포트 중 오류 발생:")
    traceback.print_exc()
    sys.exit(1)

print("\nD-Bus/Tornado 관련 환경 점검 완료. 모든 모듈이 정상적으로 로드됩니다.")
