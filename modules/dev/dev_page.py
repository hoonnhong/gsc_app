"""
dev_page.py - 개발 관리(기능/에러/메뉴) 화면 모듈
앱의 기능 요구사항, 발견된 에러, 메뉴 관리 상태 등을 기록하고 추적합니다.
"""

from nicegui import ui
import pandas as pd
from datetime import datetime
from core.db_manager import db

# 데이터베이스 테이블 초기화 (테이블이 없으면 생성)
def init_dev_table():
    db.execute("""
        CREATE TABLE IF NOT EXISTS dev_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            title TEXT,
            content TEXT,
            status TEXT DEFAULT '대기중',
            priority TEXT DEFAULT '보통',
            created_at TEXT
        )
    """)

def render_dev_page():
    """개발 관리 페이지를 렌더링합니다."""
    init_dev_table()
    
    ui.label('🛠️ 개발 및 시스템 관리').classes('text-3xl font-bold mb-4')
    
    # --- 데이터 로딩 및 요약 ---
    def get_tasks():
        return db.get_df('dev_tasks')

    def refresh_ui():
        df = get_tasks()
        # 요약 카드 업데이트
        todo_count.set_text(str(len(df[df['status'] != '완료'])))
        bug_count.set_text(str(len(df[df['category'] == '에러 보고'])))
        feature_count.set_text(str(len(df[df['category'] == '기능 추가'])))
        # 리스트 업데이트
        grid.options['rowData'] = df.to_dict('records')
        grid.update()

    with ui.row().classes('w-full gap-4 mb-6'):
        with ui.card().classes('flex-1 p-4 bg-orange-50'):
            ui.label('남은 할 일').classes('text-sm text-gray-500')
            todo_count = ui.label('0').classes('text-4xl font-bold text-orange-600')
        with ui.card().classes('flex-1 p-4 bg-red-50'):
            ui.label('보고된 에러').classes('text-sm text-gray-500')
            bug_count = ui.label('0').classes('text-4xl font-bold text-red-600')
        with ui.card().classes('flex-1 p-4 bg-blue-50'):
            ui.label('기능 요구').classes('text-sm text-gray-500')
            feature_count = ui.label('0').classes('text-4xl font-bold text-blue-600')

    # --- 신규 등록 폼 ---
    async def add_task():
        if not title_input.value:
            ui.notify('제목을 입력해주세요.', type='warning')
            return
        
        # SQL INSERT 문을 사용하여 데이터 추가 (id는 자동 생성됨)
        query = """
            INSERT INTO dev_tasks (category, title, content, status, priority, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            category_select.value,
            title_input.value,
            content_input.value,
            '대기중',
            priority_select.value,
            datetime.now().strftime('%Y-%m-%d %H:%M')
        )
        
        if db.execute(query, params):
            ui.notify('새로운 작업이 등록되었습니다!', type='positive')
            title_input.value = ''
            content_input.value = ''
            refresh_ui()
        else:
            ui.notify('저장 중 오류가 발생했습니다.', type='negative')

    with ui.expansion('🆕 새 작업 등록하기', icon='add_circle').classes('w-full bg-white mb-6 border shadow-sm'):
        with ui.column().classes('w-full p-6 gap-4'):
            with ui.row().classes('w-full gap-4'):
                category_select = ui.select(['기능 추가', '에러 보고', '메뉴 관리', '기타'], value='기능 추가', label='분류').classes('flex-1')
                priority_select = ui.select(['높음', '보통', '낮음'], value='보통', label='우선순위').classes('flex-1')
            title_input = ui.input('제목 (예: 엑셀 내보내기 기능 추가)', placeholder='여기에 제목을 입력하세요').classes('w-full')
            content_input = ui.textarea('상세 내용', placeholder='상세한 내용을 입력해주세요').classes('w-full')
            ui.button('작업 등록하기', on_click=add_task, icon='save').classes('w-full py-2')

    # --- 작업 목록 (ui.table) ---
    with ui.row().classes('w-full justify-between items-center mb-2'):
        ui.label('📝 전체 작업 내역').classes('text-xl font-bold')
        ui.label('(상태 클릭 시 진행중/완료로 변경)').classes('text-sm text-gray-400')

    columns = [
        {'name': 'id', 'label': 'ID', 'field': 'id', 'width': 50},
        {'name': 'category', 'label': '분류', 'field': 'category', 'align': 'left'},
        {'name': 'title', 'label': '제목', 'field': 'title', 'align': 'left'},
        {'name': 'status', 'label': '상태', 'field': 'status'},
        {'name': 'priority', 'label': '우선순위', 'field': 'priority'},
        {'name': 'created_at', 'label': '등록일', 'field': 'created_at'},
        {'name': 'delete', 'label': '관리', 'field': 'delete'},
    ]

    table = ui.table(columns=columns, rows=[], row_key='id').classes('w-full shadow-md border')
    
    # 테이블 행 템플릿 설정 (상태 변경 및 삭제 버튼 커스텀)
    table.add_slot('body-cell-status', """
        <q-td :props="props">
            <q-chip :color="props.value === '완료' ? 'grey' : (props.value === '진행중' ? 'blue' : 'orange')" 
                    text-color="white" clickable @click="$parent.$emit('status_click', props.row)">
                {{ props.value }}
            </q-chip>
        </q-td>
    """)
    
    table.add_slot('body-cell-delete', """
        <q-td :props="props">
            <q-btn flat round icon="delete" color="red" @click="$parent.$emit('delete_click', props.row)" />
        </q-td>
    """)

    def update_status(row):
        new_status = '진행중' if row['status'] == '대기중' else ('완료' if row['status'] == '진행중' else '대기중')
        db.execute("UPDATE dev_tasks SET status = ? WHERE id = ?", (new_status, row['id']))
        ui.notify(f'상태가 [{new_status}]로 변경되었습니다.')
        refresh_ui()

    def delete_row(row):
        db.execute("DELETE FROM dev_tasks WHERE id = ?", (row['id'],))
        ui.notify('항목이 삭제되었습니다.')
        refresh_ui()

    table.on('status_click', lambda msg: update_status(msg.args))
    table.on('delete_click', lambda msg: delete_row(msg.args))

    def refresh_ui():
        df = get_tasks()
        # 요약 카드 업데이트 (todo_count 등이 페이지 렌더링 시점에 정의되어 있어야 함)
        todo_count.set_text(str(len(df[df['status'] != '완료'])))
        bug_count.set_text(str(len(df[df['category'] == '에러 보고'])))
        feature_count.set_text(str(len(df[df['category'] == '기능 추가'])))
        # 리스트 업데이트
        table.rows = df.to_dict('records')

    # 초기 로드
    ui.timer(0.1, refresh_ui, once=True)
