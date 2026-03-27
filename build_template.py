import os

with open('e:/dev/gsc_app/modules/accounting_group/expense/final_template.html', 'r', encoding='utf-8') as f:
    html_template = f.read()

with open('e:/dev/gsc_app/modules/accounting_group/expense/row_template.txt', 'r', encoding='utf-8') as f:
    row_template = f.read()

# Make row_template generic
row_template = row_template.replace('{seq_1}', '{seq}')
row_template = row_template.replace('김명철', '{summary}')
row_template = row_template.replace('3월 25일', '{date_str}')
row_template = row_template.replace('5,180,240', '{amount}')
row_template = row_template.replace('{method_1}', '{method}')
# The empty space for note is the td with class=xl85
row_template = row_template.replace("none'>　</td>", "none'>{note}</td>")

# Generate the template.py file
py_code = f'''
import datetime

# 각 항목이 None이면 공란으로 바꿉니다.
def clean(val):
    if val is None or str(val).lower() == "none" or val == "None":
        return ""
    return str(val)

def generate_print_html(master_data, details_data, auto_print=False, hide_btn=False):
    # 결제일자를 '0000년 0월 0일' 형태로 파싱
    date_str = clean(master_data.get('approval_date', ''))
    year, month, day = "", "", ""
    if date_str:
        try:
            d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            year, month, day = d.year, d.month, d.day
        except:
            d_parts = date_str.split("-")
            if len(d_parts) == 3:
                year, month, day = d_parts[0], d_parts[1], d_parts[2]

    # 금액 포맷팅
    total_amount = int(master_data.get('total_amount', 0))
    total_amount_kr = clean(master_data.get('total_amount_kr', ''))
    total_amount_formatted = f"{{total_amount:,}}"

    # 행 생성
    row_html_template = """{row_template}"""
    
    details_rows_html = ""
    for i in range(15):
        if i < len(details_data):
            d = details_data[i]
            seq = f"{{i+1:02d}}"
            summary = clean(d.get('summary', ''))
            date_val = clean(d.get('date', ''))
            amt = int(d.get('amount', 0)) if str(d.get('amount', '0')).isdigit() else 0
            amount_str = f"{{amt:,}}" if amt > 0 else "　"
            method = clean(d.get('method', ''))
            note = clean(d.get('note', ''))
            
            # Use white spaces if empty to preserve Excel cell height/style
            if not summary: summary = "　"
            if not date_val: date_val = "　"
            if not method: method = "　"
            if not note: note = "　"
        else:
            seq, summary, date_val, amount_str, method, note = "　", "　", "　", "　", "　", "　"
            
        row_str = row_html_template.format(
            seq=seq,
            summary=summary,
            date_str=date_val,
            amount=amount_str,
            method=method,
            note=note
        )
        details_rows_html += row_str

    # 전체 HTML 치환
    final_html = """{html_template}"""
    final_html = final_html.replace('{{details_rows_html}}', details_rows_html)
    
    # 기본 정보 치환
    final_html = final_html.replace('{{title}}', clean(master_data.get('title', '')))
    final_html = final_html.replace('{{author}}', clean(master_data.get('author', '')))
    final_html = final_html.replace('{{position}}', clean(master_data.get('position', '')))
    final_html = final_html.replace('{{amount_kr}}', total_amount_kr)
    final_html = final_html.replace('{{amount_num}}', total_amount_formatted)
    
    # 날짜 치환
    if year:
        final_html = final_html.replace('{{year}}', str(year))
        final_html = final_html.replace('{{month}}', str(month))
        final_html = final_html.replace('{{day}}', str(day))
    else:
        final_html = final_html.replace('>{{year}}<', '> <')
        final_html = final_html.replace('> {{month}} <', '> <')
        final_html = final_html.replace('> {{day}} <', '> <')
        
    return final_html
'''

with open('e:/dev/gsc_app/modules/accounting_group/expense/template.py', 'w', encoding='utf-8') as f:
    f.write(py_code)

print("template.py updated successfully.")
