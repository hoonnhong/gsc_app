"""
dashboard_page.py - 메인 대시보드 화면
"""
from nicegui import ui
from core.ui_components import page_title, stat_card, card_container

def render_page():
    """기본 대시보드 화면을 렌더링합니다."""
    page_title('비즈니스 대시보드', icon='analytics')
    
    with ui.row().classes('w-full gap-6'):
        stat_card('전체 강사 수', '12명', color='blue', icon='group')
        stat_card('이번 달 강의', '24건', color='green', icon='event')
        stat_card('미지급 및 처리 대기', '5건', color='orange', icon='pending_actions')

    with card_container().classes('w-full mt-8'):
        with ui.row().classes('items-center gap-2 mb-2'):
            ui.icon('notifications_active').classes('text-2xl text-primary')
            ui.label('최근 알림').classes('text-xl font-bold text-gray-800')
        ui.separator()
        
        with ui.column().classes('w-full gap-0 mt-2'):
            notifications = [
                "박인자 강사님의 '지급 확인서'가 업로드되었습니다.",
                "신규 강의 'Python 기초'가 등록되었습니다.",
                "설정 메뉴의 UI가 지능형 시스템으로 업데이트되었습니다."
            ]
            for msg in notifications:
                with ui.row().classes('items-center gap-3 p-3 w-full hover:bg-gray-50 rounded-lg transition-colors border-b border-gray-50 last:border-0'):
                    ui.icon('check_circle', color='green').classes('text-lg')
                    ui.label(msg).classes('text-gray-700 font-medium')

