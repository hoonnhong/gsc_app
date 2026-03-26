"""
instructor_page.py - 강사/강의/지급 통합 관리 시스템
강사 기본 정보와 함께 강의 내역, 지급 서류(스캔본)를 한눈에 관리합니다.
"""

from nicegui import ui
import pandas as pd
from datetime import datetime
from core.db_manager import db
import os

def render_instructor_page():
    """강사/강의/지급 통합 관리 페이지를 렌더링합니다."""
    
    ui.label('🎓 강사 및 강의 통합 관리 시스템').classes('text-3xl font-bold mb-6')

    with ui.row().classes('w-full gap-6 items-start'):
        # --- 1. 좌측: 강사 목록 ---
        with ui.card().classes('w-1/3 p-4 shadow-lg h-[750px]'):
            ui.label('👥 강사 목록 (클릭 시 상세조회)').classes('text-xl font-bold mb-4 text-primary')
            
            columns = [
                {'name': '이름', 'label': '이름', 'field': '이름', 'align': 'left', 'sortable': True},
                {'name': '전화번호', 'label': '연락처', 'field': '전화번호', 'align': 'left'},
            ]
            
            # 강사 데이터 로드
            df_ins = db.get_df('instructors')
            rows = df_ins.to_dict('records') if not df_ins.empty else []
            
            # 테이블 클릭 시 호출될 함수
            def on_row_click(e):
                row = e.args[1]
                render_details(row['id'], row['이름'])

            table_ins = ui.table(
                columns=columns, rows=rows, row_key='id', pagination=15
            ).classes('w-full mt-2 cursor-pointer')
            
            # Quasar의 row-click 이벤트 연결
            table_ins.on('row-click', on_row_click)

            ui.button('강사 추가', icon='person_add', on_click=lambda: ui.notify('설정 메뉴에서 추가 가능합니다.')).classes('w-full mt-4 bg-green-600')

        # --- 2. 우측: 상세 정보 영역 ---
        details_area = ui.column().classes('flex-1 gap-6 h-[750px]')
        with details_area:
            ui.label('강사 목록에서 한 명을 클릭해 주세요.').classes('text-gray-400 mt-20 text-center w-full')

    def render_details(ins_id, ins_name):
        """선택된 강사의 상세 내용을 우측 영역에 수동으로 렌더링합니다."""
        details_area.clear()
        with details_area:
            # A. 강의 내역 카드
            with ui.card().classes('w-full p-6 shadow-md border-t-4 border-primary bg-white'):
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label(f'📅 [{ins_name}] 강사님 강의 내역').classes('text-xl font-bold text-primary')
                    ui.button('새 강의 등록', icon='add', on_click=lambda: open_add_dialog(ins_id, ins_name)).classes('bg-primary text-white')

                # 강의 데이터 필터링 조회
                df_lec = db.get_df('lectures')
                if not df_lec.empty and 'instructor_id' in df_lec.columns:
                    df_lec = df_lec[df_lec['instructor_id'] == ins_id]
                
                lec_columns = [
                    {'name': 'lecture_date', 'label': '날짜', 'field': 'lecture_date', 'width': 120},
                    {'name': 'title', 'label': '강의명', 'field': 'title', 'align': 'left'},
                    {'name': 'total_fee', 'label': '강의료', 'field': 'total_fee'},
                    {'name': 'status', 'label': '지급상태', 'field': 'status'},
                    {'name': 'actions', 'label': '관리', 'field': 'id'},
                ]

                # 지급 정보 병합
                lec_rows = []
                if not df_lec.empty:
                    df_pay = db.get_df('payments')
                    for _, lec in df_lec.iterrows():
                        row = lec.to_dict()
                        p = df_pay[df_pay['lecture_id'] == lec['id']] if not df_pay.empty else pd.DataFrame()
                        row['status'] = p.iloc[0]['status'] if not p.empty else '대기'
                        row['total_fee'] = f"{int(lec['total_fee'] or 0):,}원"
                        lec_rows.append(row)

                lec_table = ui.table(columns=lec_columns, rows=lec_rows, row_key='id').classes('w-full')
                
                # 상태 변경 칩
                lec_table.add_slot('body-cell-status', """
                    <q-td :props="props">
                        <q-chip :color="props.value === '완료' ? 'green-6' : (props.value === '지급중' ? 'blue-6' : 'orange-6')" 
                                text-color="white" dense clickable @click="$parent.$emit('status_click', props.row)">
                            {{ props.value }}
                        </q-chip>
                    </q-td>
                """)

                def update_pay(row):
                    new_s = '지급중' if row['status'] == '대기' else ('완료' if row['status'] == '지급중' else '대기')
                    db.execute("INSERT OR REPLACE INTO payments (lecture_id, status, updated_at) VALUES (?, ?, ?)",
                               (row['id'], new_s, datetime.now().strftime('%Y-%m-%d %H:%M')))
                    ui.notify(f'[{new_s}] 상태로 변경됨')
                    render_details(ins_id, ins_name)

                lec_table.on('status_click', lambda msg: update_pay(msg.args))

    def open_add_dialog(ins_id, ins_name):
        """강의 추가용 다이얼로그를 생성하고 엽니다."""
        with ui.dialog() as dialog, ui.card().classes('p-6 w-[400px]'):
            ui.label(f'[{ins_name}] 새로운 강의 등록').classes('text-lg font-bold mb-4')
            ti = ui.input('강의명').classes('w-full')
            dt = ui.input('날짜', value=datetime.now().strftime('%Y-%m-%d')).classes('w-full')
            fe = ui.number('강의료(원)', value=0).classes('w-full')
            
            async def save():
                if not ti.value: return
                db.execute("INSERT INTO lectures (instructor_id, title, lecture_date, total_fee) VALUES (?, ?, ?, ?)",
                           (ins_id, ti.value, dt.value, int(fe.value)))
                ui.notify('등록되었습니다.')
                dialog.close()
                render_details(ins_id, ins_name)

            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('취소', on_click=dialog.close).props('flat')
                ui.button('저장', on_click=save)
        dialog.open()
