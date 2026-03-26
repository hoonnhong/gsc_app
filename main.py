"""
main.py - 업무 관리 앱의 메인 진입점 (모듈형 통합 버전)
각 메뉴 폴더의 기능들을 불러와 하나의 포털로 구성합니다.
"""

import json
import os
from nicegui import ui
from config import Config

# 🛠️ 각 모듈의 페이지 렌더링 함수를 Import 합니다.
from modules.accounting.accounting_page import render_accounting_page
from modules.instructor.instructor_page import render_instructor_page
from modules.settings.settings_page import render_settings_page
from modules.dev.dev_page import render_dev_page

# 초기 설정 확인
Config.validate()

# --- 메뉴 데이터 로딩 ---
def load_menu_data():
    """menu.json 파일에서 메뉴 구조를 읽어옵니다."""
    menu_file = 'menu.json'
    if os.path.exists(menu_file):
        try:
            with open(menu_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"메뉴 로딩 오류: {e}")
    return []

# --- 상태 관리 (현재 어떤 메뉴를 보고 있는지) ---
class AppState:
    current_menu = 'dashboard'

state = AppState()

# --- 인터페이스 구성 ---

def build_ui():
    # 🎨 글로벌 스타일 설정 (가독성을 위해 기본 글자 크기를 18px로 상향)
    ui.add_head_html('<style>body { font-size: 18px; }</style>')
    
    # 테마 색상 설정
    ui.colors(primary='#385E3C', secondary='#F1F8E9', accent='#111B1C')
    
    # 상단 헤더
    with ui.header().classes('items-center justify-between bg-primary text-white p-4'):
        with ui.row().classes('items-center gap-6'): # 간격 소폭 확대
            ui.button(icon='menu', on_click=lambda: left_drawer.toggle()).props('flat').classes('text-white')
            ui.label('GSC 통합 업무 관리 시스템').classes('text-3xl font-bold') # 타이틀 크기 확대 (text-2xl -> text-3xl)
        
        with ui.row().classes('items-center gap-2'):
            ui.button(icon='notifications').props('flat').classes('text-white')
            ui.button(icon='account_circle').props('flat').classes('text-white')

    # 좌측 사이드바 (L자형 레이아웃)
    with ui.left_drawer(value=True).classes('bg-slate-50 border-r shadow-sm') as left_drawer:
        with ui.column().classes('w-full p-4 gap-3'): # 간격 소폭 확대
            ui.label('🏢 메인 메뉴').classes('text-sm font-bold text-gray-400 mb-2') # 라벨 크기 보강
            
            # 메뉴 생성 함수 (재귀적으로 하위 메뉴 처리 가능)
            def create_menu_item(item, depth=0):
                classes = 'w-full justify-start font-medium' # 폰트 두께 보강
                if depth > 0:
                    classes += f' pl-{depth * 8}'
                
                if 'children' in item and item['children']:
                    # 하위 메뉴 그룹
                    with ui.expansion(item['label'], icon=item['icon']).classes('w-full text-lg'): # 그룹 텍스트 크기 보강
                        for child in item['children']:
                            create_menu_item(child, depth + 1)
                else:
                    # 일반 메뉴 버튼
                    is_active = state.current_menu == item['id']
                    ui.button(item['label'], icon=item['icon'], on_click=lambda: switch_page(item['id'])) \
                        .classes(f'{classes} {"text-md" if depth > 0 else "text-lg"}') \
                        .props(f'flat icon-size="28px" {"outline" if is_active else ""}') # 아이콘 크기 및 메뉴 크기 확대

            # JSON 데이터로부터 메뉴 생성
            for menu_item in load_menu_data():
                create_menu_item(menu_item)

    # 메인 본문 컨테이너
    content_area = ui.column().classes('w-full p-8')

    def switch_page(menu_name):
        """메뉴 클릭 시 본문 내용만 교체합니다."""
        state.current_menu = menu_name
        content_area.clear()
        
        with content_area:
            if menu_name == 'dashboard':
                render_dashboard()
            elif menu_name == 'accounting':
                render_accounting_page()
            elif menu_name == 'instructor':
                render_instructor_page()
            elif menu_name == 'settings':
                render_settings_page()
            elif menu_name == 'dev':
                render_dev_page()
            else:
                ui.label(f'"{menu_name}" 페이지는 준비 중입니다.').classes('text-xl text-gray-400')

    def render_dashboard():
        """기본 대시보드 화면"""
        ui.markdown('### 👋 안녕하세요, 대표님!').classes('mb-6 text-xl') # 텍스트 크기 확대
        with ui.row().classes('w-full gap-6'):
            with ui.card().classes('w-80 p-6 border-l-8 border-primary'): # 카드 크기 및 테두리 확대
                ui.label('오늘의 일정').classes('text-lg font-bold text-gray-500')
                ui.label('0건').classes('text-4xl font-black text-primary')
            with ui.card().classes('w-80 p-6 border-l-8 border-blue-500'):
                ui.label('미결재').classes('text-lg font-bold text-gray-500')
                ui.label('3건').classes('text-4xl font-black text-blue-600')

    # 최초 실행 시 대시보드 표시
    switch_page('dashboard')

@ui.page('/')
def index():
    build_ui()

# --- 앱 실행 설정 ---
# 이 부분이 있어야 웹 서버가 실제로 시작됩니다.
# Windows 환경에서의 멀티프로세싱(재시작 기능 등) 호환을 위해 '__mp_main__'을 포함합니다.
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='GSC App', port=8080, language='ko-KR')
