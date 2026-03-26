"""
settings_page.py - 시스템 설정 및 메뉴 편집 화면
메뉴 구조(JSON)를 수정하고 앱의 전반적인 설정을 관리합니다.
"""

from nicegui import ui
import json
import os

from core.ai_helper import ai

def render_settings_page():
    """설정 페이지를 렌더링합니다."""
    ui.label('⚙️ 시스템 설정 및 관리').classes('text-3xl font-bold mb-4')
    
    with ui.tabs().classes('w-full') as tabs:
        menu_tab = ui.tab('메뉴 및 모듈 편집')
        general_tab = ui.tab('시스템 정보')

    with ui.tab_panels(tabs, value=menu_tab).classes('w-full bg-transparent'):
        with ui.tab_panel(menu_tab):
            render_menu_editor()
        with ui.tab_panel(general_tab):
            ui.label('GSC 통합 업무 관리 시스템 v1.5').classes('text-gray-500')

def render_menu_editor():
    """AI 연동 메뉴 편집기를 렌더링합니다."""
    menu_file = 'menu.json'
    
    def load_menu():
        if os.path.exists(menu_file):
            with open(menu_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def ensure_module_exists(menu_id):
        """메뉴 ID에 해당하는 모듈 폴더와 파일을 생성합니다 (없을 경우만)"""
        module_dir = os.path.join('modules', menu_id)
        if not os.path.exists(module_dir):
            os.makedirs(module_dir)
            ui.notify(f'[{menu_id}] 폴더가 생성되었습니다.', type='info')
        
        file_path = os.path.join(module_dir, f'{menu_id}_page.py')
        if not os.path.exists(file_path):
            template = f'"""\n{menu_id}_page.py - 자동 생성된 모듈\n"""\nfrom nicegui import ui\n\ndef render_page():\n    ui.label("{menu_id} 페이지가 생성되었습니다.").classes("text-2xl font-bold")\n    ui.notify("코드를 수정하여 기능을 완성해 주세요.")\n'
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template)
            ui.notify(f'[{menu_id}_page.py] 템플릿 파일이 생성되었습니다.', type='positive')

    def save_all_menu(data):
        # 1. JSON 저장
        with open(menu_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 2. 각 메뉴별 모듈 파일 생성 확인 (재귀)
        def process_items(items):
            for item in items:
                m_id = item.get('id')
                if m_id and m_id != 'new':
                    ensure_module_exists(m_id)
                if 'children' in item:
                    process_items(item['children'])
        
        process_items(data)
        ui.notify('모든 설정과 모듈 파일이 업데이트되었습니다. 다시 로트 하세요.', type='positive')

    state = {'menu': load_menu()}
    editor_container = ui.column().classes('w-full gap-4')

    def refresh_editor():
        editor_container.clear()
        with editor_container:
            for index, item in enumerate(state['menu']):
                render_item_editor(item, state['menu'], index)
            
            with ui.row().classes('w-full justify-between mt-8 p-4 bg-white shadow rounded-lg'):
                ui.button('새 메인 메뉴 추가', icon='add', on_click=add_main_menu).classes('bg-green-600 px-6')
                ui.button('변경사항 전체 저장 및 모듈 생성', icon='cloud_upload', 
                          on_click=lambda: save_all_menu(state['menu'])).classes('bg-primary px-6 py-2 font-bold')

    def render_item_editor(item, parent_list, index, depth=0):
        with ui.card().classes(f'w-full p-4 {"ml-12 border-l-4 border-blue-200" if depth > 0 else "border-l-8 border-primary"} shadow-sm mb-2'):
            with ui.row().classes('w-full items-center gap-4'):
                # 순서 조절
                with ui.column().classes('gap-0'):
                    ui.button(icon='arrow_drop_up', on_click=lambda: move_item(parent_list, index, -1)).props('flat dense')
                    ui.button(icon='arrow_drop_down', on_click=lambda: move_item(parent_list, index, 1)).props('flat dense')
                
                # 라벨 입력
                lbl = ui.input('메뉴 이름', value=item.get('label', '')).bind_value(item, 'label').classes('w-48')
                
                # AI 추천 버튼
                async def suggest_ai(target_item):
                    if not target_item.get('label'):
                        ui.notify('먼저 메뉴 이름을 입력해 주세요.', type='warning')
                        return
                    ui.notify('제미나이가 추천 중입니다...', type='info')
                    res = ai.get_menu_recommendation(target_item['label'])
                    if res:
                        target_item['id'] = res['id']
                        target_item['icon'] = res['icon']
                        ui.notify(f"추천 완료: {res['id']} / {res['icon']}")
                        refresh_editor()
                    else:
                        ui.notify('AI 추천에 실패했습니다. API 키를 확인하세요.', type='negative')

                ui.button(icon='psychology', on_click=lambda: suggest_ai(item)).props('flat dense').classes('text-blue-500').tooltip('AI로 ID와 아이콘 추천받기')

                # ID 및 아이콘
                ui.input('ID', value=item.get('id', '')).bind_value(item, 'id').classes('w-32')
                ui.input('아이콘', value=item.get('icon', '')).bind_value(item, 'icon').classes('w-32')
                
                ui.space()
                ui.button(icon='delete', color='red', on_click=lambda: delete_item(parent_list, index)).props('flat dense')
            
            # 자식 메뉴들
            if 'children' in item:
                for c_idx, child in enumerate(item['children']):
                    render_item_editor(child, item['children'], c_idx, depth + 1)
                
            # 하위 메뉴 추가
            with ui.row().classes('w-full justify-start mt-2 border-t pt-2'):
                ui.button('하위 메뉴 추가', icon='add_circle_outline', 
                          on_click=lambda: add_child_menu(item)).props('flat dense').classes('text-blue-600')

    def move_item(lst, idx, direction):
        new_idx = idx + direction
        if 0 <= new_idx < len(lst):
            lst[idx], lst[new_idx] = lst[new_idx], lst[idx]
            refresh_editor()

    def delete_item(lst, idx):
        lst.pop(idx)
        refresh_editor()

    def add_main_menu():
        state['menu'].append({'id': '', 'label': '', 'icon': 'star'})
        refresh_editor()

    def add_child_menu(item):
        if 'children' not in item:
            item['children'] = []
        item['children'].append({'id': '', 'label': '', 'icon': 'arrow_right'})
        refresh_editor()

    refresh_editor()
