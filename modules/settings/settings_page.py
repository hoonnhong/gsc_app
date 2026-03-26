"""
settings_page.py - 시스템 설정 및 메뉴 편집 화면
메뉴 구조(JSON)를 수정하고 앱의 전반적인 설정을 관리합니다.
"""

from nicegui import ui
import json
import os

def render_settings_page():
    """설정 페이지를 렌더링합니다."""
    ui.label('⚙️ 시스템 설정').classes('text-3xl font-bold mb-4')
    
    with ui.tabs().classes('w-full') as tabs:
        menu_tab = ui.tab('메뉴 편집')
        general_tab = ui.tab('일반 설정')

    with ui.tab_panels(tabs, value=menu_tab).classes('w-full'):
        with ui.tab_panel(menu_tab):
            render_menu_editor()
        with ui.tab_panel(general_tab):
            ui.label('일반 설정 기능은 준비 중입니다.')

def render_menu_editor():
    """메뉴 편집기를 렌더링합니다."""
    menu_file = 'menu.json'
    
    def load_menu():
        if os.path.exists(menu_file):
            with open(menu_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_menu(data):
        with open(menu_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        ui.notify('메뉴 설정이 저장되었습니다. 앱을 새로고침하세요.', type='positive')

    state = {'menu': load_menu()}

    ui.markdown('#### 📱 메뉴 구조 편집').classes('mb-4')
    
    editor_container = ui.column().classes('w-full gap-4')

    def refresh_editor():
        editor_container.clear()
        with editor_container:
            for index, item in enumerate(state['menu']):
                render_item_editor(item, state['menu'], index)
            
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('새 메뉴 추가', icon='add', on_click=add_main_menu).classes('bg-green-600')
                ui.button('전체 저장', icon='save', on_click=lambda: save_menu(state['menu'])).classes('bg-primary')

    def render_item_editor(item, parent_list, index, depth=0):
        with ui.card().classes(f'w-full p-4 {"ml-8" if depth > 0 else ""}'):
            with ui.row().classes('w-full items-center gap-4'):
                # 순서 변경 버튼
                with ui.column().classes('gap-1'):
                    ui.button(icon='expand_less', on_click=lambda: move_item(parent_list, index, -1)).props('flat dense')
                    ui.button(icon='expand_more', on_click=lambda: move_item(parent_list, index, 1)).props('flat dense')
                
                # 입력 필드
                ui.input('이름', value=item.get('label', '')).bind_value(item, 'label').classes('w-40')
                ui.input('아이콘', value=item.get('icon', '')).bind_value(item, 'icon').classes('w-32')
                ui.input('ID', value=item.get('id', '')).bind_value(item, 'id').classes('w-32')
                
                # 삭제 버튼
                ui.space()
                ui.button(icon='delete', color='red', on_click=lambda: delete_item(parent_list, index)).props('flat dense')
            
            # 하위 메뉴들
            if 'children' in item:
                for c_idx, child in enumerate(item['children']):
                    render_item_editor(child, item['children'], c_idx, depth + 1)
                
            # 하위 메뉴 추가 버튼
            with ui.row().classes('w-full justify-start mt-2'):
                ui.button('하위 메뉴 추가', icon='subdirectory_arrow_right', 
                          on_click=lambda: add_child_menu(item)).props('flat dense').classes('text-xs text-blue-600')

    def move_item(lst, idx, direction):
        new_idx = idx + direction
        if 0 <= new_idx < len(lst):
            lst[idx], lst[new_idx] = lst[new_idx], lst[idx]
            refresh_editor()

    def delete_item(lst, idx):
        lst.pop(idx)
        refresh_editor()

    def add_main_menu():
        state['menu'].append({'id': 'new', 'label': '새 메뉴', 'icon': 'star'})
        refresh_editor()

    def add_child_menu(item):
        if 'children' not in item:
            item['children'] = []
        item['children'].append({'id': 'new_sub', 'label': '새 하위 메뉴', 'icon': 'arrow_right'})
        refresh_editor()

    refresh_editor()
