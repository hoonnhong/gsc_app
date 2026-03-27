import re

with open('e:/dev/gsc_app/modules/accounting_group/expense/processed_template.html', 'r', encoding='utf-8') as f:
    text = f.read()

# '순번', '적 요' 등 헤더 행 다음부터 15개 행을 찾기 위해
# 우선 {seq_1}이 있는 tr의 시작 위치를 찾습니다.
seq1_idx = text.find('{seq_1}')
# 그 앞의 가장 가까운 <tr 을 찾습니다.
tr_start = text.rfind('<tr', 0, seq1_idx)

# 이제 여기서부터 15개의 </tr>을 찾아서 전체를 {details_rows_html}로 바꿀 것입니다.
current_pos = tr_start
for _ in range(15):
    end_idx = text.find('</tr>', current_pos)
    if end_idx == -1:
        break
    current_pos = end_idx + 5

# 추출할 1번째 Row 템플릿 (CSS 클래스명 등을 알기 위해)
row1_html = text[tr_start : text.find('</tr>', tr_start) + 5]

# 기존 15개 행 부분 전체를 날리고 placeholder 삽입
first_part = text[:tr_start]
second_part = text[current_pos:]
new_text = first_part + '{details_rows_html}' + second_part

with open('e:/dev/gsc_app/modules/accounting_group/expense/final_template.html', 'w', encoding='utf-8') as f:
    f.write(new_text)

with open('e:/dev/gsc_app/modules/accounting_group/expense/row_template.txt', 'w', encoding='utf-8') as f:
    f.write(row1_html)

print("done")
