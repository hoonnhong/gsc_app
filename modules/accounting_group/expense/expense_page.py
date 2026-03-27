"""
expense_page.py - 지출품의서 앱 (NiceGUI + SQLite 기반)
"""
import base64
import pandas as pd
from datetime import datetime
from nicegui import ui

# 공통 모듈 및 로컬 작성 모듈
from core.db_manager import db
from modules.accounting_group.expense.utils import to_korean_amount, format_date_str
from modules.accounting_group.expense.template import generate_print_html

# ==========================================
# 데이터베이스 연동 함수 (SQLite)
# ==========================================

def load_all_reports():
    masters_df = db.get_df('expense_masters')
    details_df = db.get_df('expense_details')
    
    if masters_df.empty:
        return []
    
    reports = []
    for _, master_row in masters_df.iterrows():
        master_dict = master_row.to_dict()
        if not details_df.empty and 'master_id' in details_df.columns:
            m_id = master_dict.get('master_id')
            master_details = details_df[details_df['master_id'] == m_id].to_dict('records')
            master_dict['details'] = master_details
        else:
            master_dict['details'] = []
        reports.append(master_dict)
    
    # 내림차순 정렬 (최신 번호 상단)
    reports.sort(key=lambda x: x.get('master_id', ''), reverse=True)
    return reports

def get_new_master_id():
    masters_df = db.get_df('expense_masters')
    if masters_df.empty or 'master_id' not in masters_df.columns:
        return "EXP-001"
    
    max_num = 0
    for idx in masters_df['master_id']:
        try:
            num = int(str(idx).split('-')[1])
            if num > max_num: max_num = num
        except:
            pass
    return f"EXP-{max_num + 1:03d}"

def save_expense_report(master_data, details_data):
    try:
        new_id = get_new_master_id()
        master_data['master_id'] = new_id
        
        # Details 채우기
        valid_details = []
        for d in details_data:
            summary = d.get('summary', '').strip()
            amount = int(d.get('amount', 0))
            if summary or amount > 0:
                d_copy = d.copy()
                d_copy['master_id'] = new_id
                valid_details.append(d_copy)
                
        # 기존 데이터 불러오기 및 추가
        masters_df = db.get_df('expense_masters')
        details_df = db.get_df('expense_details')
        
        m_df = pd.DataFrame([master_data])
        d_df = pd.DataFrame(valid_details)
        
        new_masters_df = pd.concat([masters_df, m_df], ignore_index=True) if not masters_df.empty else m_df
        new_details_df = pd.concat([details_df, d_df], ignore_index=True) if not details_df.empty else d_df
        
        db.save_df(new_masters_df, 'expense_masters')
        db.save_df(new_details_df, 'expense_details')
        return new_id
    except Exception as e:
        return f"오류: {e}"

def delete_expense_report(master_id):
    masters_df = db.get_df('expense_masters')
    details_df = db.get_df('expense_details')
    
    if not masters_df.empty and 'master_id' in masters_df.columns:
        masters_df = masters_df[masters_df['master_id'] != master_id]
        db.save_df(masters_df, 'expense_masters')
        
    if not details_df.empty and 'master_id' in details_df.columns:
        details_df = details_df[details_df['master_id'] != master_id]
        db.save_df(details_df, 'expense_details')
    return True

# ==========================================
# UI 렌더링 함수
# ==========================================

def render_expense_page():
    ui.label('📄 지출품의서 시스템 (DB 연동)').classes('text-3xl font-bold mb-4')
    
    with ui.tabs().classes('w-full') as tabs:
        new_tab = ui.tab('📝 신규 작성')
        manage_tab = ui.tab('🔍 내역 관리')
    
    with ui.tab_panels(tabs, value=new_tab).classes('w-full bg-transparent p-0 mt-4'):
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
        'details': [{'summary': '', 'date': '', 'amount': None, 'method': '', 'note': ''} for _ in range(5)]
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
        new_preview_iframe.props(f'src="data:text/html;base64,{b64_html}"')
        total_label.set_text(f"총 금액: {total:,}원")

    # 상단에 "과거 내역 불러오기" 버튼 배치
    with ui.expansion('📑 과거 내역 불러오기 (복사해서 작성)', icon='history').classes('w-full mb-4 bg-blue-50 rounded-lg shadow-sm'):
        ui.label('준비 중인 기능입니다. (DB에서 이전 내역을 선택하여 채우는 기능)')

    # 좌우 분할 레이아웃 (PC 작업 효율 최적화)
    with ui.row().classes('w-full items-start gap-4 no-wrap'):
        # 1. 좌측 영역: 정보 입력 (전체 너비의 약 42%)
        with ui.column().classes('w-full md:w-[42%] gap-4'):
            with ui.column().classes('w-full p-6 bg-white shadow-md rounded-xl border border-gray-100'):
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('1. 기본 정보 및 상세 내역').classes('text-2xl font-bold text-gray-800')
                    
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
                    
                    ui.button('💾 품의서 저장', on_click=do_save).classes('bg-red-500 text-white shadow-lg').props('icon="save"')
                
                with ui.row().classes('w-full gap-4 items-center mb-4'):
                    author_input = ui.input('기안자').bind_value(state, 'author').classes('flex-1').props('outlined dense')
                    pos_input = ui.input('직급').bind_value(state, 'position').classes('flex-1').props('outlined dense')
                
                date_input = ui.input('결제일자').bind_value(state, 'approval_date').classes('w-full mb-4').props('outlined dense type="date"')
                title_input = ui.input('품의제목', placeholder='예: 3월 급여').bind_value(state, 'title').classes('w-full mb-6').props('outlined dense')
                
                ui.label('2. 상세 지출내역').classes('text-xl font-bold mb-3 text-gray-700')
                
                @ui.refreshable
                def grid():
                    with ui.column().classes('w-full gap-2'):
                        for i, row in enumerate(state['details']):
                            with ui.row().classes('w-full items-center gap-2 p-2 bg-gray-50 rounded-lg border border-gray-200'):
                                ui.input('적요').bind_value(row, 'summary').classes('flex-1').props('dense borderless').on('change', update_preview)
                                ui.input('일자').bind_value(row, 'date').classes('w-20').props('dense borderless placeholder="M-D"').on('change', update_preview)
                                ui.input('금액').props('type="number" placeholder="0" dense borderless').bind_value(row, 'amount').classes('w-24').on('change', update_preview)
                                ui.input('지급방법').bind_value(row, 'method').classes('w-24').props('dense borderless').on('change', update_preview)
                                ui.input('비고').bind_value(row, 'note').classes('w-20').props('dense borderless').on('change', update_preview)
                    
                    with ui.row().classes('w-full justify-center mt-3'):
                        def add_row():
                            state['details'].append({'summary': '', 'date': '', 'amount': None, 'method': '', 'note': ''})
                            grid.refresh()
                        ui.button('➕ 줄 추가', on_click=add_row).props('flat color="primary" icon="add"')
                
                grid()
                
                ui.label('3. 비고란').classes('text-xl font-bold mt-6 mb-2 text-gray-700')
                note_input = ui.textarea('텍스트 본문').bind_value(state, 'note_text').classes('w-full').props('outlined rows=5').on('change', update_preview)
                
                def handle_upload(e):
                    b64 = base64.b64encode(e.content.read()).decode()
                    state['note_image_b64'] = b64
                    update_preview()
                    ui.notify('이미지가 첨부되었습니다.')
                    
                ui.upload(label='이미지 첨부 (*.PNG, JPG)', on_upload=handle_upload, auto_upload=True).classes('w-full mt-4').props('outlined dense accept="image/*"')
                
                # 입력 바인딩으로 미리보기 자동 갱신
                author_input.on('change', update_preview)
                pos_input.on('change', update_preview)
                title_input.on('change', update_preview)
                date_input.on('change', update_preview)

        # 2. 우측 영역: A4 미리보기 (전체 너비의 약 58%, 스크롤 시 고정)
        with ui.column().classes('w-full md:w-[58%] sticky top-4 gap-4'):
            with ui.column().classes('w-full p-4 bg-blue-50 rounded-xl shadow-inner border border-blue-100 items-center'):
                with ui.row().classes('w-full justify-between items-center mb-4 px-2'):
                    ui.label('4. 출력 미리보기 (A4)').classes('text-2xl font-bold text-blue-900')
                    total_label = ui.label('총 결제금액: 0원').classes('text-xl font-bold text-red-600')
                    
                    def do_print():
                        print_js = """
                        var iframe = document.getElementById('new-preview-iframe');
                        if (iframe && iframe.src.startsWith('data:')) {
                            var printWindow = window.open('', '', 'width=1000,height=1200');
                            var b64 = iframe.src.split(',')[1];
                            var bin = atob(b64);
                            var u8 = new Uint8Array(bin.length);
                            for (var i=0; i<bin.length; i++) u8[i] = bin.charCodeAt(i);
                            var html = new TextDecoder('utf-8').decode(u8);
                            printWindow.document.write(html);
                            printWindow.document.close();
                            printWindow.onload = function() { 
                                setTimeout(function() { printWindow.print(); }, 500);
                            };
                        }
                        """
                        ui.run_javascript(print_js)
                        
                    ui.button('🖨️ 인쇄 진행 (새 창)', on_click=do_print).classes('bg-blue-800 text-white shadow-md').props('icon="print"')
                
                # A4 용지 규격을 시뮬레이션하는 카드
                with ui.card().classes('w-full max-w-[210mm] p-0 shadow-2xl bg-white border border-gray-300 transform scale-90 origin-top'):
                    new_preview_iframe = ui.element('iframe').classes('w-full').style('height: 297mm; border: none;')
                    new_preview_iframe.props('id="new-preview-iframe"')
                
    # 초기 실행 및 프리뷰 로드
    update_preview()

@ui.refreshable
def render_manage_reports_tab():
    reports = load_all_reports()
    
    if not reports:
        ui.label('저장된 내역이 없습니다.').classes('text-gray-500 mt-4')
        return
        
    ui.label(f'총 {len(reports)}건의 품의서가 있습니다.').classes('text-lg font-bold mb-4')
    
    # 간이 리스트/테이블
    columns = [
        {'name': 'master_id', 'label': '문서번호', 'field': 'master_id', 'sortable': True},
        {'name': 'approval_date', 'label': '결제일자', 'field': 'approval_date', 'sortable': True},
        {'name': 'title', 'label': '품의제목', 'field': 'title'},
        {'name': 'author', 'label': '기안자', 'field': 'author'},
        {'name': 'total_amount', 'label': '금액', 'field': 'total_amount'}
    ]
    
    rows = []
    for r in reports:
        rows.append({
            'master_id': r.get('master_id'),
            'approval_date': r.get('approval_date'),
            'title': r.get('title'),
            'author': r.get('author'),
            'total_amount': f"{int(r.get('total_amount', 0)):,}원"
        })
        
    table = ui.table(columns=columns, rows=rows, row_key='master_id').classes('w-full mb-8 shadow-sm')
    
    ui.markdown('---')
    ui.label('문서 조회 및 인쇄').classes('text-xl font-bold mt-4')
    
    sel_options = {r['master_id']: f"[{r['master_id']}] {r.get('title')}" for r in reports}
    
    state = {'selected': list(sel_options.keys())[0] if sel_options else None}
    
    # 글로벌 대신 로컬 컨테이너 사용 (멀티세션 안전)
    view_container_wrapper = ui.column().classes('w-full mt-4')
    
    def update_view():
        if not state['selected']: return
        
        # 로딩 중임을 알림 (디버깅 겸용)
        # ui.notify(f'문서 {state["selected"]} 로드 중...', type='info', duration=1)
        
        target = next((x for x in reports if x['master_id'] == state['selected']), None)
        if target:
            # 상세 정보가 없는 경우를 대비해 다시 로드 (DB 최신화 반영)
            html_content = generate_print_html(target, target.get('details', []), hide_btn=True)
            # base64 방식으로 주입
            b64_html = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
            manage_preview_iframe.props(f'src="data:text/html;base64,{b64_html}"')
        else:
            ui.notify('해당 문서를 찾을 수 없습니다.', type='negative')
            
    with ui.row().classes('w-full items-center gap-4'):
        # on_change=update_view를 직접 할당하여 즉각적인 갱신 보장
        select = ui.select(options=sel_options, label='문서 번호 선택', on_change=update_view).bind_value(state, 'selected').classes('flex-1')
        
        def do_delete():
            if state['selected']:
                delete_expense_report(state['selected'])
                ui.notify(f'{state["selected"]} 삭제 완료', type='positive')
                render_manage_reports_tab.refresh()
                
        ui.button('❌ 선택 문서 삭제', on_click=do_delete).classes('bg-red-500 text-white')
        
        def do_print_manage():
            print_js = """
            var iframe = document.getElementById('manage-preview-iframe');
            if (iframe && iframe.src.startsWith('data:')) {
                var printWindow = window.open('', '', 'width=1000,height=1200');
                var b64 = iframe.src.split(',')[1];
                var bin = atob(b64);
                var u8 = new Uint8Array(bin.length);
                for (var i=0; i<bin.length; i++) u8[i] = bin.charCodeAt(i);
                var html = new TextDecoder('utf-8').decode(u8);
                printWindow.document.write(html);
                printWindow.document.close();
                printWindow.onload = function() { 
                    setTimeout(function() { 
                        printWindow.print(); 
                    }, 500);
                };
            }
            """
            ui.run_javascript(print_js)
            
        ui.button('🖨️ 인쇄 (새 창)', on_click=do_print_manage).classes('bg-blue-600 text-white')

    # 문서 조회 및 인쇄 컨테이너와 iframe 미리 생성
    with ui.card().classes('w-full min-height-[297mm] p-0 mx-auto shadow-xl bg-white'):
        manage_preview_iframe = ui.element('iframe').classes('w-full').style('height: 297mm; border: none;')
        manage_preview_iframe.props('id="manage-preview-iframe"')
    
    update_view() # 초기 렌더링
