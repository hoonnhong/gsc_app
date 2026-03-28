"""
main.py - 업무 관리 앱의 메인 진입점 (모듈형 통합 버전)
각 메뉴 폴더의 기능들을 불러와 하나의 포털로 구성합니다.
"""

import json
import os
from nicegui import ui
from config import Config

from core.ui_components import apply_global_css
from core.router import PageRouter
from core.auth import is_authenticated, logout, has_permission
from modules.auth.login_page import render_login_page

# 🛠️ 각 모듈의 페이지 렌더링 함수 동적 임포트로 대체됨 (core.router.PageRouter 사용)

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
from nicegui import app

# --- 인터페이스 구성 ---

@ui.refreshable
def render_sidebar():
    """좌측 사이드바 메뉴를 렌더링합니다."""
    with ui.column().classes('w-full p-4 gap-3'):
        ui.label('🏢 메인 메뉴').classes('text-sm font-bold text-gray-400 mb-2')
        
        def create_menu_item(item, depth=0):
            # 권한 체크: 아이템 ID가 권한 목록에 있거나 admin인 경우만 렌더링
            if not has_permission(item['id']):
                return

            classes = 'w-full justify-start font-medium'
            if depth > 0:
                classes += f' pl-{depth * 8}'
            
            if 'children' in item and item['children']:
                # 자식 메뉴 중 권한이 있는 것이 하나라도 있는 경우만 확장 메뉴 렌더링
                visible_children = [c for c in item['children'] if has_permission(c['id'])]
                if not visible_children:
                    return
                    
                with ui.expansion(item['label'], icon=item['icon']).classes('w-full text-lg'):
                    for child in visible_children:
                        create_menu_item(child, depth + 1)
            else:
                try:
                    current = app.storage.user.get('current_menu', 'dashboard')
                except RuntimeError:
                    current = 'dashboard'
                is_active = current == item['id']
                ui.button(item['label'], icon=item['icon'], on_click=lambda id=item['id']: switch_page(id)) \
                    .classes(f'{classes} {"text-md" if depth > 0 else "text-lg"}') \
                    .props(f'flat icon-size="28px" {"outline" if is_active else ""}')

        for menu_item in load_menu_data():
            create_menu_item(menu_item)

@ui.refreshable
def render_content(menu_name):
    """메인 콘텐츠 영역을 렌더링합니다."""
    with ui.column().classes('flex-grow p-8 bg-gray-50 overflow-auto w-full min-h-screen'):
        # 동적 라우터를 통해 페이지 로드
        PageRouter.load_page(menu_name)

def switch_page(menu_name):
    """페이지를 전환합니다."""
    try:
        app.storage.user['current_menu'] = menu_name
    except RuntimeError:
        pass
    render_sidebar.refresh()
    render_content.refresh(menu_name)

def build_ui():
    # 저장된 폰트 크기 가져오기 (기본값 16px로 조정, 모던 웹 표준)
    try:
        font_size = app.storage.user.get('font_size', 16)
    except RuntimeError:
        font_size = 16
    
    # 새로운 모던 디자인 시스템 CSS 적용
    apply_global_css(font_size)
    
    with ui.header().classes('items-center justify-between text-white p-4 shadow-md bg-primary'):
        with ui.row().classes('items-center gap-6'):
            ui.button(icon='menu', on_click=lambda: left_drawer.toggle()).props('flat').classes('text-white')
            ui.label('GSC 통합 업무 관리 시스템').classes('text-3xl font-bold')
        
        # 우측 사용자 정보 및 로그아웃 버튼
        with ui.row().classes('items-center gap-4'):
            try:
                user_name = app.storage.user.get('user_name', '사용자')
                ui.label(f'👤 {user_name}님').classes('text-sm font-medium opacity-90')
            except RuntimeError:
                pass
            ui.button('로그아웃', icon='logout', on_click=logout).classes('bg-white text-primary rounded-lg font-bold px-4 h-10')
    
    # 사이드바 너비를 350px로 더 여유롭게 확장
    with ui.left_drawer(value=True).classes('bg-slate-50 border-r shadow-sm').props('width=350') as left_drawer:
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
    if not is_authenticated():
        ui.open('/login')
        return
    build_ui()

@ui.page('/login')
def login_page():
    render_login_page()

if __name__ in {"__main__", "__mp_main__"}:
    # 상태 유지를 위해 storage_secret 설정
    # reconnect_timeout을 늘려 handshake failed 오류 방지 시도
    ui.run(title='GSC App', port=8080, language='ko-KR', storage_secret='gsc_secret_key_123', reconnect_timeout=10)