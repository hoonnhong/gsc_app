
import datetime
import os
from jinja2 import Template

def clean(val):
    if val is None or str(val).lower() == "none" or val == "None":
        return ""
    return str(val)

def generate_print_html(master_data, details_data, auto_print=False, hide_btn=False):
    """
    지출품의서 출력을 위한 HTML을 생성합니다 (별도 파일 템플릿 사용).
    """
    # 1. 템플릿 파일 로드
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'expense_report_template.html')
    if not os.path.exists(template_path):
        # 템플릿 파일이 없을 경우 대비 (안전장치)
        return "템플릿 파일을 찾을 수 없습니다: " + template_path
        
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # 2. 렌더링을 위한 데이터 가공
    date_str = clean(master_data.get('approval_date', ''))
    
    # 작성 날짜 (오늘 날짜 기준)
    today = datetime.datetime.now()
    year, month, day = today.year, today.month, today.day
    
    # 기안 데이터
    total_amount = int(master_data.get('total_amount', 0))
    total_amount_kr = clean(master_data.get('total_amount_kr', ''))
    total_amount_formatted = f"{total_amount:,} 원"
    
    # 상세 내역 처리 (최대 7줄)
    items = []
    for i in range(len(details_data)):
        if i >= 7: break # 템플릿 제약
        d = details_data[i]
        try:
            raw_amt = d.get('amount', 0)
            amt = int(raw_amt) if str(raw_amt).isdigit() or isinstance(raw_amt, (int, float)) else 0
        except:
            amt = 0
        amt_str = f"{amt:,}" if amt > 0 else ""
        
        items.append({
            'seq': i + 1,
            'summary': clean(d.get('summary', '')),
            'date': clean(d.get('date', '')),
            'amount': amt_str,
            'method': clean(d.get('method', '')),
            'note': clean(d.get('note', ''))
        })

    # 템플릿에 전달할 컨텍스트 구성
    context = {
        '결재_담당': clean(master_data.get('sign_manager', '')),
        '결재_경영이사': clean(master_data.get('sign_director', '')),
        '결재_이사장': clean(master_data.get('sign_ceo', '')),
        '품의제목': clean(master_data.get('title', '')),
        '결제일자': date_str,
        '기안자': clean(master_data.get('author', '')),
        '기안자_직급': clean(master_data.get('position', '')),
        '품의총금액': f"{total_amount_kr} ({total_amount_formatted})",
        '합계금액': total_amount_formatted,
        '문서비고': clean(master_data.get('note_text', '')),
        '작성년도': year,
        '작성월': month,
        '작성일': day,
        '신청인': clean(master_data.get('author', '')),
        'items': items  # 리스트로 전달
    }

    # 만약 템플릿에 개별 변수({{ 순번_1 }} 등)가 쓰였다면 아래와 같이 추가 매핑
    for i in range(1, 8):
        if (i - 1) < len(items):
            item = items[i-1]
            context[f'순번_{i}'] = item['seq']
            context[f'적요_{i}'] = item['summary']
            context[f'일자_{i}'] = item['date']
            context[f'금액_{i}'] = item['amount']
            context[f'지급방법_{i}'] = item['method']
            context[f'항목비고_{i}'] = item['note']
        else:
            context[f'순번_{i}'] = ""
            context[f'적요_{i}'] = ""
            context[f'일자_{i}'] = ""
            context[f'금액_{i}'] = ""
            context[f'지급방법_{i}'] = ""
            context[f'항목비고_{i}'] = ""

    # 3. Jinja2를 이용한 렌더링
    template = Template(template_content)
    rendered_html = template.render(context)

    # 4. 자동 인쇄 스크립트 추가
    if auto_print:
        print_script = "<script>window.onload = function() { window.print(); };</script>"
        rendered_html = rendered_html.replace('</body>', f'{print_script}</body>')

    return rendered_html
