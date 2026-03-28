"""
expense_page.py - 지출품의서 앱 (NiceGUI + SQLite 기반)
"""
import base64
import pandas as pd
import os
import shutil
from datetime import datetime
from nicegui import ui

# 공통 모듈 및 로컬 작성 모듈
from core.db_manager import db
from core.ui_components import page_title, primary_button, error_button, card_container
from core.utils import to_korean_amount, format_date_str, get_print_javascript
from modules.accounting_group.expense.template import generate_print_html
from modules.accounting_group.expense.expense_repo import (
    load_all_reports, get_new_master_id, save_expense_report, delete_expense_report, update_scan_path
)

# ==========================================
# UI 렌더링 함수
# ==========================================

def render_expense_page():
    # 상단 영역 (타이틀 좌측, 탭 중앙 배치)
    with ui.row().classes('w-full items-center justify-center relative mb-1 px-2'):
        # 타이틀 (좌측 고정)
        with ui.row().classes('absolute left-2 items-center gap-2'):
            ui.icon('description').classes('text-2xl text-primary')
            ui.label('지출품의서 시스템 (DB 연동)').classes('text-xl font-bold text-gray-800')
        
        # 탭 메뉴 (가운데 정렬 및 강조)
        with ui.tabs().classes('bg-transparent') as tabs:
            new_tab = ui.tab('📝 신규 작성').classes('text-lg font-bold px-8')
            manage_tab = ui.tab('🔍 내역 관리').classes('text-lg font-bold px-8')
    
    with ui.tab_panels(tabs, value=new_tab).classes('w-full bg-transparent p-0 mt-0'):
        with ui.tab_panel(new_tab):
            render_new_report_tab()
        with ui.tab_panel(manage_tab):
            render_manage_reports_tab()

def render_new_report_tab():
    # 상태 변수 (dict 래핑)
    state = {
        'author': '',
        'position': '',
        'title': '',
        'approval_date': datetime.now().strftime('%Y-%m-%d'),
        'note_text': '',
        'note_image_b64': '',
        'details': [{'summary': '', 'date': '', 'amount': None, 'method': '', 'note': ''} for _ in range(5)],
        'iframe': None  # 미리보기 iframe 참조 보관용
    }
    
    def update_preview():
        # 상세 내역 날짜 형식 자동 변환 (M-D -> M월 D일)
        for row in state['details']:
            d_val = str(row.get('date', '')).strip()
            if '-' in d_val and '월' not in d_val:
                parts = d_val.split('-')
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    row['date'] = f"{parts[0]}월 {parts[1]}일"

        total = sum(int(d.get('amount') or 0) for d in state['details'])
        m_data = {
            'title': state['title'],
            'author': state['author'],
            'position': state['position'],
            'approval_date': state['approval_date'],
            'total_amount': total,
            'total_amount_kr': to_korean_amount(total),
            'note_text': state['note_text'],
            'note_image_b64': state['note_image_b64']
        }
        
        d_list = []
        for d in state['details']:
            if str(d.get('summary', '')).strip() or int(d.get('amount') or 0) > 0:
                d_list.append({
                    'summary': d.get('summary', ''),
                    'date': format_date_str(d.get('date', '')),
                    'amount': int(d.get('amount', 0)),
                    'method': d.get('method', ''),
                    'note': d.get('note', '')
                })
        
        html_content = generate_print_html(m_data, d_list, hide_btn=True)
        # 줄바꿈 문자가 JS 전송 시 오류를 유발할 수 있으므로 제거 후 base64 인코딩
        b64_html = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
        
        # iframe이 생성된 후에만 속성 업데이트 (NameError 방지)
        if state['iframe']:
            state['iframe'].props(f'src="data:text/html;base64,{b64_html}"')
        
        total_label.set_text(f"총 금액: {total:,}원")

    # 상단에 "과거 내역 불러오기" 버튼 배치 (더 작게 조정)
    with ui.expansion('📑 과거 내역 불러오기 (복사)', icon='history').classes('w-full mb-2 bg-blue-50 rounded-lg shadow-sm font-sm').props('dense'):
        ui.label('준비 중인 기능입니다. (DB에서 이전 내역을 선택하여 채우는 기능)').classes('text-xs p-2')

    # 좌우 분할 레이아웃 (높이 균형 조정: items-stretch)
    with ui.row().classes('w-full items-stretch gap-2 no-wrap'):
        # 1. 좌측 영역: 정보 입력
        with ui.column().classes('w-full md:w-[42%] gap-2'):
            with ui.column().classes('w-full h-full p-3 bg-white shadow-md rounded-xl border border-gray-100'):
                with ui.row().classes('w-full justify-between items-center mb-2'):
                    ui.label('1. 기본 정보 및 상세 내역').classes('text-lg font-bold text-gray-800')
                    
                    def do_save():
                        if not state['title'] or not state['author']:
                            ui.notify('오류: 품의제목과 기안자를 입력하세요.', type='negative')
                            return
                        
                        total = sum(int(d['amount']) for d in state['details'] if d['amount'])
                        if total == 0:
                            ui.notify('오류: 지출 금액이 0원입니다.', type='negative')
                            return
                        
                        m_data = {
                            'title': state['title'],
                            'author': state['author'],
                            'position': state['position'],
                            'approval_date': state['approval_date'],
                            'total_amount': total,
                            'total_amount_kr': to_korean_amount(total),
                            'note_text': state['note_text'],
                            'note_image_b64': state['note_image_b64'],
                            'scan_file_path': ''
                        }
                        
                        res = save_expense_report(m_data, state['details'])
                        if '오류' in res:
                            ui.notify(res, type='negative')
                        else:
                            ui.notify(f'✅ 저장 성공! (문서번호: {res})', type='positive')
                        
                    primary_button('품의서 저장', on_click=do_save, icon='save')
                
                with ui.row().classes('w-full gap-2 items-center mb-2'):
                    author_input = ui.input('기안자').bind_value(state, 'author').classes('flex-1').props('dense')
                    pos_input = ui.input('직급').bind_value(state, 'position').classes('flex-1').props('dense')
                
                date_input = ui.input('결재일자').bind_value(state, 'approval_date').classes('w-full mb-2').props('type="date" dense')
                title_input = ui.input('품의제목', placeholder='예: 3월 급여').bind_value(state, 'title').classes('w-full mb-4').props('dense')
                
                ui.label('2. 상세 지출내역').classes('text-md font-bold mb-1 text-gray-700')
                
                @ui.refreshable
                def grid():
                    with ui.column().classes('w-full gap-2 border rounded-lg bg-gray-50/50 p-2'):
                        for i, row in enumerate(state['details']):
                            with ui.row().classes('w-full items-center gap-1 p-0.5 bg-white rounded-md shadow-sm border border-gray-100'):
                                ui.input('적요').bind_value(row, 'summary').classes('flex-1').props('dense borderless').on('change', update_preview)
                                ui.input('일자').bind_value(row, 'date').classes('w-16').props('dense borderless placeholder="M-D"').on('change', update_preview)
                                ui.input('금액').props('type="number" dense borderless').bind_value(row, 'amount').classes('w-20').on('change', update_preview)
                                ui.input('지급방법').bind_value(row, 'method').classes('w-16').props('dense borderless').on('change', update_preview)
                                ui.input('비고').bind_value(row, 'note').classes('w-16').props('dense borderless').on('change', update_preview)
                    
                    with ui.row().classes('w-full justify-center mt-2'):
                        def add_row():
                            state['details'].append({'summary': '', 'date': '', 'amount': None, 'method': '', 'note': ''})
                            grid.refresh()
                        ui.button('➕ 줄 추가', on_click=add_row).props('flat color="primary" size="sm"')
                
                grid()
                
                ui.label('3. 비고란').classes('text-md font-bold mt-4 mb-1 text-gray-700')
                note_input = ui.textarea('텍스트 본문').bind_value(state, 'note_text').classes('w-full').props('rows=2 dense').on('change', update_preview)
                
                def handle_upload(e):
                    b64 = base64.b64encode(e.content.read()).decode()
                    state['note_image_b64'] = b64
                    update_preview()
                    ui.notify('이미지가 첨부되었습니다.')
                    
                ui.upload(label='이미지 첨부 (*.PNG, JPG)', on_upload=handle_upload, auto_upload=True).classes('w-full mt-4').props('accept="image/*"')
                
                # 입력 바인딩으로 미리보기 자동 갱신
                author_input.on('change', update_preview)
                pos_input.on('change', update_preview)
                title_input.on('change', update_preview)
                date_input.on('change', update_preview)

        # 2. 우측 영역: A4 미리보기
        with ui.column().classes('w-full md:w-[58%] sticky top-2 gap-2'):
            with card_container().classes('w-full h-full shadow-inner border-blue-50 items-center bg-blue-50/10 p-2'):
                with ui.row().classes('w-full justify-between items-center mb-2 px-1'):
                    ui.label('4. 출력 미리보기 (A4)').classes('text-lg font-bold text-gray-800')
                    total_label = ui.label('총 금액: 0원').classes('text-md font-bold text-red-600')
                    
                    def do_print():
                        ui.run_javascript(get_print_javascript('new-preview-iframe'))
                        
                    primary_button('인쇄 진행', on_click=do_print, icon='print').classes('bg-gray-800 text-white shadow-none')
                
                # A4 용지 규격을 시뮬레이션하는 카드 (축소 비율 조정: 한 화면에 다 보이게)
                with ui.card().classes('w-full max-w-[210mm] p-0 shadow-lg bg-white border border-gray-200 transform scale-[0.55] origin-top md:scale-[0.6] xl:scale-[0.7] mb-[-180px] px-0'):
                    state['iframe'] = ui.element('iframe').classes('w-full').style('height: 297mm; border: none; overflow: hidden;')
                    state['iframe'].props('id="new-preview-iframe" scrolling="no"')
                
    # 초기 실행 및 프리뷰 로드
    update_preview()

@ui.refreshable
def render_manage_reports_tab():
    all_reports = load_all_reports()
    
    # 검색 필터 상태
    search_state = {
        'title': '',
        'author': '',
        'date_start': '',
        'date_end': '',
        'min_amount': None,
        'max_amount': None
    }
    
    # 현재 선택된 문서 상태 (딕셔너리로 관리하여 클로저 이슈 방지)
    state = {
        'selected_id': all_reports[0]['master_id'] if all_reports else None,
        'iframe': None,
        'scan_folder': './scans/expenses/'
    }

    def get_filtered_reports():
        filtered = all_reports
        if search_state['title']:
            filtered = [r for r in filtered if search_state['title'].lower() in r.get('title', '').lower()]
        if search_state['author']:
            filtered = [r for r in filtered if search_state['author'].lower() in r.get('author', '').lower()]
        if search_state['date_start']:
            filtered = [r for r in filtered if r.get('approval_date', '') >= search_state['date_start']]
        if search_state['date_end']:
            filtered = [r for r in filtered if r.get('approval_date', '') <= search_state['date_end']]
        if search_state['min_amount'] is not None:
            filtered = [r for r in filtered if int(r.get('total_amount', 0)) >= search_state['min_amount']]
        if search_state['max_amount'] is not None:
            filtered = [r for r in filtered if int(r.get('total_amount', 0)) <= search_state['max_amount']]
        return filtered

    def get_filtered_rows():
        f = get_filtered_reports()
        return [{
            'master_id': r.get('master_id'),
            'approval_date': r.get('approval_date'),
            'title': r.get('title'),
            'author': r.get('author'),
            'total_amount': f"{int(r.get('total_amount', 0)):,}원"
        } for r in f]

    def update_view():
        if not state['selected_id'] or not state['iframe']: return
        
        target = next((x for x in all_reports if x['master_id'] == state['selected_id']), None)
        if target:
            html_content = generate_print_html(target, target.get('details', []), hide_btn=True)
            b64_html = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
            state['iframe'].props(f'src="data:text/html;base64,{b64_html}"')
            
            # 스캔 관리 UI 상태 업데이트
            scan_path = target.get('scan_file_path')
            scan_info_label.set_text(f"📁 현재 파일: {os.path.basename(scan_path) if scan_path else '없음'}")
            open_scan_btn.set_visibility(bool(scan_path and os.path.exists(scan_path)))
        else:
            ui.notify('해당 문서를 찾을 수 없습니다.', type='negative')

    with ui.row().classes('w-full no-wrap items-stretch gap-2'):
        # ==========================================
        # 1. 좌측 영역: 목록 및 검색 (약 40%)
        # ==========================================
        with ui.column().classes('w-full md:w-[40%] gap-4'):
            with ui.card().classes('w-full h-full p-4 shadow-md bg-gray-50 border-none'):
                ui.label('🔍 내역 필터링').classes('text-lg font-bold mb-2 text-gray-700')
                with ui.row().classes('w-full gap-2 items-center'):
                    ui.input('품의제목', on_change=lambda: table.set_rows(get_filtered_rows())).bind_value(search_state, 'title').classes('flex-1').props('dense outlined bg-color=white')
                    ui.input('기안자', on_change=lambda: table.set_rows(get_filtered_rows())).bind_value(search_state, 'author').classes('flex-1').props('dense outlined bg-color=white')
                with ui.row().classes('w-full gap-2 items-center'):
                    ui.input('시작일', on_change=lambda: table.set_rows(get_filtered_rows())).props('type=date dense outlined bg-color=white').bind_value(search_state, 'date_start').classes('flex-1')
                    ui.input('종료일', on_change=lambda: table.set_rows(get_filtered_rows())).props('type=date dense outlined bg-color=white').bind_value(search_state, 'date_end').classes('flex-1')
                with ui.row().classes('w-full gap-2 items-center mb-4'):
                    ui.number('최소 금액', on_change=lambda: table.set_rows(get_filtered_rows())).bind_value(search_state, 'min_amount').classes('flex-1').props('dense outlined bg-color=white')
                    ui.number('최대 금액', on_change=lambda: table.set_rows(get_filtered_rows())).bind_value(search_state, 'max_amount').classes('flex-1').props('dense outlined bg-color=white')

                columns = [
                    {'name': 'master_id', 'label': '번호', 'field': 'master_id', 'sortable': True, 'align': 'left'},
                    {'name': 'approval_date', 'label': '일자', 'field': 'approval_date', 'sortable': True},
                    {'name': 'title', 'label': '제목', 'field': 'title', 'align': 'left'},
                    {'name': 'author', 'label': '기안자', 'field': 'author'},
                    {'name': 'total_amount', 'label': '금액', 'field': 'total_amount', 'align': 'right'}
                ]
                
                table = ui.table(columns=columns, rows=get_filtered_rows(), row_key='master_id').classes('w-full shadow-sm sticky top-0')
                # 행 클릭 시 해당 문서로 미리보기 업데이트
                table.on('rowClick', lambda e: (state.update({'selected_id': e.args[1]['master_id']}), update_view()))
                
                with ui.row().classes('w-full justify-between items-center mt-2 px-1'):
                    ui.label(f'총 {len(all_reports)}건 중 필터링됨').classes('text-gray-500 text-sm')
                    
                    def do_delete():
                        if state['selected_id']:
                            delete_expense_report(state['selected_id'])
                            ui.notify(f'{state["selected_id"]} 삭제 완료', type='positive')
                            render_manage_reports_tab.refresh()
                        else:
                            ui.notify('삭제할 문서를 선택하세요.', type='warning')
                    
                    error_button('선택 문서 삭제', on_click=do_delete, icon='delete').props('flat')

        # ==========================================
        # 2. 우측 영역: 미리보기 및 스캔 관리 (약 60%)
        # ==========================================
        with ui.column().classes('w-full md:w-[60%] gap-4'):
            with ui.card().classes('w-full h-full p-4 shadow-inner bg-slate-50 border-none'):
                with ui.row().classes('w-full justify-between items-center mb-2 px-2'):
                    ui.label('📄 문서 미리보기 및 인쇄').classes('text-xl font-bold text-slate-800')
                    
                    def do_print():
                        ui.run_javascript(get_print_javascript('manage-preview-iframe'))
                    
                    primary_button('인쇄 진행', on_click=do_print, icon='print').classes('bg-slate-800 shadow-none text-white')
                
                # 스캔 파일 관리 섹션 (상단으로 이동)
                with ui.expansion('📎 스캔된 결재문서 관리', icon='cloud_upload').classes('w-full mb-4 bg-white rounded-xl border border-blue-100 shadow-sm'):
                    with ui.column().classes('w-full p-4 gap-4'):
                        ui.input('📂 스캔본 저장 폴더').bind_value(state, 'scan_folder').classes('w-full').props('outlined dense')
                        
                        with ui.row().classes('w-full items-center justify-between p-3 bg-blue-50/30 rounded-lg'):
                            scan_info_label = ui.label('현재 파일: 없음').classes('text-blue-900 font-medium')
                            
                            def open_file():
                                target = next((x for x in all_reports if x['master_id'] == state['selected_id']), None)
                                path = target.get('scan_file_path')
                                if path and os.path.exists(path):
                                    ui.notify(f'파일을 엽니다: {os.path.basename(path)}')
                                    os.startfile(os.path.abspath(path)) # Windows 전용
                                else:
                                    ui.notify('파일이 없거나 경로가 잘못되었습니다.', type='negative')
                            
                            open_scan_btn = ui.button('파일 열기', on_click=open_file, icon='open_in_new').classes('bg-blue-600 text-white')

                        def handle_upload(e):
                            if not state['selected_id']:
                                ui.notify('먼저 문서를 선택하세요.', type='warning')
                                return
                            
                            # 저장 디렉토리 생성
                            save_dir = state['scan_folder']
                            if not os.path.exists(save_dir):
                                os.makedirs(save_dir)
                            
                            # 파일명 생성: EXP-001_기안자_제목.ext
                            target = next((x for x in all_reports if x['master_id'] == state['selected_id']), None)
                            safe_title = "".join(x for x in target['title'] if x.isalnum() or x in " -_").strip()
                            ext = os.path.splitext(e.name)[1]
                            filename = f"{state['selected_id']}_{target['author']}_{safe_title}{ext}"
                            dest_path = os.path.join(save_dir, filename)
                            
                            try:
                                with open(dest_path, 'wb') as f:
                                    f.write(e.content.read())
                                
                                # DB 정보 업데이트
                                update_scan_path(state['selected_id'], dest_path)
                                ui.notify(f'✅ 스캔본이 저장되었습니다: {filename}', type='positive')
                                render_manage_reports_tab.refresh()
                            except Exception as ex:
                                ui.notify(f'❌ 저장 실패: {ex}', type='negative')

                        ui.upload(label='스캔된 파일 업로드 (*.pdf, *.jpg, *.png)', on_upload=handle_upload, auto_upload=True).classes('w-full').props('outlined dense')

                # A4 용지 규격을 시뮬레이션하는 카드
                with ui.card().classes('w-full max-w-[210mm] p-0 shadow-2xl bg-white border border-gray-200 transform scale-[0.55] lg:scale-[0.65] origin-top mx-auto mb-[-120px]'):
                    state['iframe'] = ui.element('iframe').classes('w-full').style('height: 297mm; border: none; overflow: hidden;')
                    state['iframe'].props('id="manage-preview-iframe" scrolling="no"')

    # 초기 데이터 로드 시 미리보기 실행
    update_view()
