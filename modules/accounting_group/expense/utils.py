# 이 파일은 애플리케이션 전반에서 공통으로 사용되는 유틸리티 함수들을 모아둔 모듈입니다.

def to_korean_amount(amount):
    """숫자를 한글 법정 금액으로 변환합니다. (예: 50,000 -> 일금 오만원정)"""
    if not amount or amount == 0:
        return "일금 0원정"
    
    han_numbers = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
    units = ["", "십", "백", "천"]
    big_units = ["", "만", "억", "조"]
    
    num_str = str(int(amount))
    result = ""
    num_len = len(num_str)
    
    for i in range(num_len):
        num = int(num_str[i])
        unit_idx = (num_len - 1 - i) % 4
        big_unit_idx = (num_len - 1 - i) // 4
        
        if num != 0:
            result += han_numbers[num] + units[unit_idx]
            
        if unit_idx == 0:
            # 4자리마다 '만', '억' 등을 붙여줍니다.
            if result and result[-1] in big_units:
                continue
            result += big_units[big_unit_idx]
                
    return "일금 " + result + "원정"

def format_date_str(val):
    """'YYYY-MM-DD' 형식의 날짜 문자열을 'M월 D일' 형식으로 변환합니다."""
    if not val or not isinstance(val, str): return val
    if "-" in val:
        parts = val.split("-")
        if len(parts) == 2: # MM-DD 형식
            try:
                return f"{int(parts[0])}월 {int(parts[1])}일"
            except:
                pass
        elif len(parts) == 3: # YYYY-MM-DD 형식 (데이터 에디터에서 입력될 때)
            try:
                return f"{int(parts[1])}월 {int(parts[2])}일"
            except:
                pass
    return val
