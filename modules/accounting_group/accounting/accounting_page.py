from nicegui import ui
from core.db_manager import db # 로컬 DB 매니저 사용

def render_accounting_page():
    """회계 관리 페이지를 렌더링합니다."""
    # 데이터 불러오기
    df = db.get_df('accounting')
    
    # 총 지출액 계산 (간단한 예시)
    total_expense = 0
    if not df.empty and '금액' in df.columns:
        total_expense = df['금액'].sum()

    ui.label('💰 회계 관리 시스템 (로컬 DB)').classes('text-3xl font-bold mb-4')
    
    with ui.row().classes('w-full gap-6'):
        with ui.card().classes('flex-1 p-6 border-l-8 border-red-500 shadow-lg'):
            ui.label('이번 달 지출 현황').classes('text-lg font-semibold mb-2')
            ui.label(f'{total_expense:,}원').classes('text-4xl font-black text-red-600')
            ui.button('지출 결의서 작성', icon='edit_note').classes('mt-4 w-full bg-red-600 text-white')

        with ui.card().classes('flex-1 p-6 border-l-8 border-blue-500 shadow-lg'):
            ui.label('예산 잔액 (예시)').classes('text-lg font-semibold mb-2')
            remaining = 12500000 - total_expense
            ui.label(f'{remaining:,}원').classes('text-4xl font-black text-blue-600')
            ui.button('상세 장부 보기', icon='visibility').classes('mt-4 w-full bg-blue-600 text-white')

    # 데이터 테이블 표시
    if not df.empty:
        with ui.card().classes('w-full mt-6 p-4'):
            ui.label('최근 지출 내역').classes('text-xl font-bold mb-4')
            ui.table(columns=[{'name': col, 'label': col, 'field': col} for col in df.columns],
                     rows=df.to_dict('records')).classes('w-full')
