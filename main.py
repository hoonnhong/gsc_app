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
# app.storage.user에 저장하여 새로고침 후에도 유지되도록 합니다.
from nicegui import app

# --- 인터페이스 구성 ---

@ui.refreshable
def render_sidebar():
    """좌측 사이드바 메뉴를 렌더링합니다."""
    with ui.column().classes('w-full p-4 gap-3'):
        ui.label('🏢 메인 메뉴').classes('text-sm font-bold text-gray-400 mb-2')
        
        def create_menu_item(item, depth=0):
            classes = 'w-full justify-start font-medium'
            if depth > 0:
                classes += f' pl-{depth * 8}'
            
            if 'children' in item and item['children']:
                with ui.expansion(item['label'], icon=item['icon']).classes('w-full text-lg'):
                    for child in item['children']:
                        create_menu_item(child, depth + 1)
            else:
                # 현재 선택된 메뉴인지 확인
                try:
                    current = app.storage.user.get('current_menu', 'dashboard')
                except RuntimeError:
                    current = 'dashboard'
                is_active = current == item['id']
                ui.button(item['label'], icon=item['icon'], on_click=lambda: switch_page(item['id'])) \
                    .classes(f'{classes} {"text-md" if depth > 0 else "text-lg"}') \
                    .props(f'flat icon-size="28px" {"outline" if is_active else ""}')

        for menu_item in load_menu_data():
            create_menu_item(menu_item)

@ui.refreshable
def render_content(menu_name):
    """메인 콘텐츠 영역을 렌더링합니다."""
    with ui.column().classes('flex-grow p-8 bg-gray-50 overflow-auto w-full'):
        import importlib
        try:
            module_path = f'modules.{menu_name}.{menu_name}_page'
            module = importlib.import_module(module_path)
            
            if hasattr(module, 'render_page'):
                module.render_page()
            elif hasattr(module, f'render_{menu_name}_page'):
                getattr(module, f'render_{menu_name}_page')()
            else:
                with ui.column().classes('w-full mt-20 items-center'):
                    ui.icon('warning', size='64px', color='orange')
                    ui.label(f'"{menu_name}" 모듈 실행 함수 없음').classes('text-xl mt-4')
        except ImportError:
            with ui.column().classes('w-full mt-20 items-center text-gray-400'):
                ui.icon('construction', size='80px')
                ui.label(f'[{menu_name}] 기능 개발 중입니다.').classes('text-2xl font-bold mt-4')
                if menu_name == 'settings':
                    from modules.settings.settings_page import render_settings_page
                    render_settings_page()
        except Exception as e:
            ui.label(f'오류 발생: {str(e)}').classes('text-red-600')

def switch_page(menu_name):
    """페이지를 전환합니다."""
    try:
        app.storage.user['current_menu'] = menu_name
    except RuntimeError:
        pass
    render_sidebar.refresh()
    render_content.refresh(menu_name)

def build_ui():
    ui.add_head_html('<style>body { font-size: 18px; }</style>')
    ui.colors(primary='#385E3C', secondary='#F1F8E9', accent='#111B1C')
    
    with ui.header().classes('items-center justify-between bg-primary text-white p-4'):
        with ui.row().classes('items-center gap-6'):
            ui.button(icon='menu', on_click=lambda: left_drawer.toggle()).props('flat').classes('text-white')
            ui.label('GSC 통합 업무 관리 시스템').classes('text-3xl font-bold')
    
    with ui.left_drawer(value=True).classes('bg-slate-50 border-r shadow-sm') as left_drawer:
        render_sidebar()

    # 콘텐츠 영역
    container = ui.column().classes('w-full')
    with container:
        try:
            current = app.storage.user.get('current_menu', 'dashboard')
        except RuntimeError:
            current = 'dashboard' # 스토리지 미준비 시 기본값
        render_content(current)

def refresh_app_sidebar():
    """외부 모듈에서 호출 가능한 사이드바 갱신 함수입니다."""
    render_sidebar.refresh()

@ui.page('/')
def index():
    build_ui()

if __name__ in {"__main__", "__mp_main__"}:
    # 상태 유지를 위해 storage_secret 설정
    ui.run(title='GSC App', port=8080, language='ko-KR', storage_secret='gsc_secret_key_123')
