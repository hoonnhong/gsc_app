"""
dashboard_page.py - 메인 대시보드 화면
"""
from nicegui import ui

def render_page():
    """기본 대시보드 화면을 렌더링합니다."""
    ui.label('📊 비즈니스 대시보드').classes('text-3xl font-bold mb-6')
    
    with ui.row().classes('w-full gap-6'):
        with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-blue-50 to-blue-100 shadow-sm border-l-4 border-blue-500'):
            ui.label('전체 강사 수').classes('text-gray-500 font-medium')
            ui.label('12명').classes('text-4xl font-black text-blue-700 mt-2')
            
        with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-green-50 to-green-100 shadow-sm border-l-4 border-green-500'):
            ui.label('이번 달 강의').classes('text-gray-500 font-medium')
            ui.label('24건').classes('text-4xl font-black text-green-700 mt-2')
            
        with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-orange-50 to-orange-100 shadow-sm border-l-4 border-orange-500'):
            ui.label('미지급 및 처리 대기').classes('text-gray-500 font-medium')
            ui.label('5건').classes('text-4xl font-black text-orange-700 mt-2')

    with ui.card().classes('w-full mt-8 p-8 bg-white border border-gray-100 rounded-xl shadow-sm'):
        ui.label('🚀 최근 알림').classes('text-xl font-bold mb-4')
        ui.separator()
        with ui.column().classes('w-full gap-3 mt-4'):
            for msg in [
                "박인자 강사님의 '지급 확인서'가 업로드되었습니다.",
                "신규 강의 'Python 기초'가 등록되었습니다.",
                "설정 메뉴의 UI가 지능형 시스템으로 업데이트되었습니다."
            ]:
                with ui.row().classes('items-center gap-2 p-2 hover:bg-gray-50 rounded-lg transition-colors'):
                    ui.icon('check_circle', color='blue')
                    ui.label(msg).classes('text-gray-700')
