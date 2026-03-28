"""
ui_components.py - 애플리케이션 공통 UI 디자인 컴포넌트 모듈
Tailwind를 활용한 일관된 디자인 시스템 적용 및 중복 코드 최소화를 담당합니다.
"""
from nicegui import ui

class Theme:
    """테마 색상 및 공통 스타일 상수를 정의합니다."""
    PRIMARY = '#385E3C'
    SECONDARY = '#F1F8E9'
    ACCENT = '#111B1C'
    
    CARD_CLASSES = 'p-6 bg-white border border-gray-100 rounded-xl shadow-sm hover:shadow-md transition-shadow'
    TITLE_CLASSES = 'text-2xl font-bold text-gray-800'
    SUBTITLE_CLASSES = 'text-lg font-semibold text-gray-600 mb-4'

def apply_global_css(font_size=16):
    """
    기존 main.py의 강제 폰트 설정을 대체하는 모던하고 부드러운 전역 CSS 설정
    과도한 !important를 피하고 컴포넌트 계층을 존중합니다.
    """
    ui.add_head_html(f'''
        <style>
            :root {{
                --gsc-primary: {Theme.PRIMARY};
                --gsc-secondary: {Theme.SECONDARY};
                --gsc-bg: #f8fafc;
                --gsc-text: #1e293b;
            }}
            body {{
                font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
                background-color: var(--gsc-bg);
                color: var(--gsc-text);
                font-size: {font_size}px;
            }}
            
            /* 입력창 크기 보정 */
            .q-field__control {{
                height: 40px !important;
                border-radius: 6px !important;
            }}
            
            /* 스크롤바 디자인 */
            ::-webkit-scrollbar {{
                width: 8px;
                height: 8px;
            }}
            ::-webkit-scrollbar-track {{
                background: #f1f1f1; 
                border-radius: 4px;
            }}
            ::-webkit-scrollbar-thumb {{
                background: #c1c1c1; 
                border-radius: 4px;
            }}
            ::-webkit-scrollbar-thumb:hover {{
                background: #a8a8a8; 
            }}
        </style>
    ''')
    ui.colors(primary=Theme.PRIMARY, secondary=Theme.SECONDARY, accent=Theme.ACCENT)

def page_title(text: str, icon: str = None):
    """표준 페이지 타이틀 컴포넌트"""
    with ui.row().classes('items-center gap-3 mb-6'):
        if icon:
            ui.icon(icon).classes('text-3xl text-primary')
        ui.label(text).classes(Theme.TITLE_CLASSES)

def card_container():
    """기본 카드 컨테이너를 반환합니다. (with 구문 사용)"""
    return ui.card().classes(Theme.CARD_CLASSES)

def stat_card(title: str, value: str, color: str = 'blue', icon: str = None):
    """대시보드 등에서 사용하는 통계 카드"""
    classes = f'flex-1 p-6 bg-gradient-to-br from-{color}-50 to-{color}-100 shadow-sm border-l-4 border-{color}-500 rounded-xl'
    with ui.card().classes(classes):
        with ui.row().classes('w-full justify-between items-start'):
            ui.label(title).classes('text-gray-500 font-medium')
            if icon:
                ui.icon(icon).classes(f'text-2xl text-{color}-400 opacity-50')
        ui.label(value).classes(f'text-4xl font-black text-{color}-700 mt-2')

def primary_button(text: str, on_click, icon: str = None):
    """주요 액션 버튼 (저장, 등록 등)"""
    btn = ui.button(text, on_click=on_click).classes('bg-primary text-white shadow-md font-medium px-4 py-2 rounded-lg hover:bg-opacity-90')
    if icon:
        btn.props(f'icon="{icon}"')
    return btn

def error_button(text: str, on_click, icon: str = None):
    """삭제, 취소 등경고성 버튼"""
    btn = ui.button(text, on_click=on_click).classes('bg-red-500 text-white shadow-md font-medium px-4 py-2 rounded-lg hover:opacity-90')
    if icon:
        btn.props(f'icon="{icon}"')
    return btn
