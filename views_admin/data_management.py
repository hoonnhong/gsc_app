import streamlit as st
import math
import pandas as pd
import time
from services.migration_service import MigrationService

def show():
    st.title("💾 데이터 관리 (Data Management)")
    
    # 탭 구성 (확장성 고려)
    tab1, tab2, tab3, tab4 = st.tabs(["💰 회계 자료", "👥 조합원 자료", "🏥 한의원 환자", "💊 한의원 판매"])
    
    with tab1:
        _render_accounting_tab()
    
    with tab2:
        st.info("🚧 조합원 자료 마이그레이션 준비 중")
        
    with tab3:
        st.info("🚧 한의원 환자 자료 마이그레이션 준비 중")
        
    with tab4:
        st.info("🚧 한의원 판매 자료 마이그레이션 준비 중")

def _render_accounting_tab():
    """회계 자료 탭 렌더링"""
    st.markdown("### 📥 회계 엑셀 업로드")
    st.caption("기존 데이터에 새로운 엑셀 파일 내용을 **추가(Append)** 합니다. 업로드 후 중복 데이터를 확인하세요.")

    # 파일 업로드 (Sidebar가 아닌 메인 화면에 배치하여 탭별 컨텍스트 유지)
    uploaded_file = st.file_uploader("회계 엑셀 파일 (.xlsx)", type=['xlsx'], key="acc_uploader")
    
    if uploaded_file:
        # 파일 ID 생성 (중복 처리 방지)
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        
        # 버튼을 눌러야 실행되도록 변경 (실수 방지)
        if st.button("🔄 데이터 변환 및 저장 시작", type="primary"):
            with st.spinner("데이터 정제 및 DB 변환 중..."):
                try:
                    count = MigrationService.process_accounting_data(uploaded_file)
                    st.success(f"✅ 처리 완료! 총 {count}건이 추가되었습니다.")
                    st.session_state['acc_last_update'] = file_id # 갱신 트리거
                    st.session_state['show_duplicate_check'] = True # 중복 확인 자동 활성화
                except Exception as e:
                    st.error(f"❌ 처리 중 오류 발생: {e}")

    st.divider()

    # 중복 데이터 관리 (NEW)
    _render_duplicate_manager()
    
    st.divider()
    
    # 데이터 조회 (Paging)
    _render_accounting_table()

def _render_duplicate_manager():
    """중복 데이터 확인 및 수정"""
    st.markdown("### ⚠️ 중복 데이터 관리")
    st.info("💡 **안내**: 중복된 데이터 중 하나를 삭제하여 1건만 남게 되면, 더 이상 중복이 아니므로 **이 목록에서 사라지고** 전체 데이터 목록에만 남습니다.")
    
    col_dup_header, col_dup_btn = st.columns([8, 2])
    with col_dup_btn:
        if st.button("🔄 목록 새로고침", key="refresh_dup"):
            st.rerun()
    
    # 중복 확인 자동 펼치기 로직
    default_expanded = st.session_state.get('show_duplicate_check', False)
    
    # 삭제 성공 메시지 표시 (Rerun 후)
    if 'dup_msg' in st.session_state:
        st.success(st.session_state['dup_msg'])
        del st.session_state['dup_msg']
    
    with st.expander("중복 의심 데이터 확인하기 (동일한 날짜, 목, 세목, 적요, 금액)", expanded=default_expanded):
        df_dup = MigrationService.get_duplicates()
        
        if df_dup.empty:
            st.success("중복된 데이터가 발견되지 않았습니다. ✅")
        else:
            st.warning(f"총 {len(df_dup)}건의 중복 의심 데이터가 발견되었습니다.")
            st.markdown("아래 테이블에서 데이터를 직접 **수정**하거나 **삭제**할 수 있습니다.")
            
            # 편집용 데이터프레임 (ID는 수정 불가)
            column_map = {
                'id': 'ID',
                'type': '수입/지출', 'gwan': '관', 'hang': '항', 'mok': '목', 'semok': '세목',
                'detail_1': '상세1', 'detail_2': '상세2', 'detail_3': '상세3', 'detail_4': '상세4',
                'amount': '금액', 'account_name': '계좌명', 'reg_date': '등기일'
            }
            
            edited_df = st.data_editor(
                df_dup.rename(columns=column_map),
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",

                key=f"dup_editor_{len(df_dup)}", # 데이터 개수가 바뀌면 컴포넌트 강제 리렌더링
                disabled=["ID"] # ID 수정 방지
            )
            
            # 변경 사항 적용 (Diff check is tricky with data_editor key state, 
            # but st.data_editor returns the current state.
            # To handle real DB updates, we need to compare or use on_change callback.
            # Streamlit data_editor handles state internally. 
            # We need a proper commit button or detect changes.)
            
            # st.data_editor's output `edited_df` is just the dataframe state.
            # It doesn't tell us WHAT changed easily unless we compare.
            # BUT, data_editor has `num_rows="dynamic"` which allows add/delete.
            # Actually, `experimental_data_editor` changed to `data_editor`.
            # We can use `on_change` with `st.session_state`.
            
    # NOTE: Real-time DB update with data_editor is complex in standard Streamlit pattern without Session State hacking.
    # Simplified approach: "Check inconsistencies" -> Show table -> "User manages ID-based actions separately?"
    # Better: Use `st.data_editor` return value and a "Save Changes" button.
    # But `data_editor` returns the final dataframe. We need to know what to UPDATE/DELETE.
    
    # Revised Approach for Simplicity & Stability:
    # Just list them. Provide 'Delete' button per row? No, too many rows.
    # Provide a simple "Delete All Duplicates (Keep One)"? Dangerous.
    # Let's use the layout requested: "Color display -> Modify/Delete".
    
            # st.data_editor에서 삭제/수정된 내용 처리
            # deleted_rows는 session_state의 editor key에 저장됨
            if f"dup_editor_{len(df_dup)}" in st.session_state:
                editor_state = st.session_state[f"dup_editor_{len(df_dup)}"]
                
                # 삭제된 행 처리
                deleted_rows = editor_state.get("deleted_rows", [])
                if deleted_rows:
                    # 삭제된 행의 인덱스를 이용하여 실제 데이터프레임에서 ID를 찾음
                    # df_dup는 0부터 시작하는 RangeIndex를 가지고 있다고 가정하면 안됨.
                    # data_editor의 deleted_rows 인덱스는 표시된 df의 행 번호임.
                    
                    # 삭제된 행의 ID 수집
                    deleted_ids = []
                    for row_idx in deleted_rows:
                        # df_dup의 해당 row_idx 행을 가져옴
                        deleted_id = df_dup.iloc[row_idx]['id']
                        deleted_ids.append(int(deleted_id))
                    
                    if deleted_ids:
                        for del_id in deleted_ids:
                            MigrationService.delete_transaction(del_id)
                        
                        st.session_state['dup_msg'] = f"총 {len(deleted_ids)}건 삭제 완료. (사라진 데이터가 DB에서 제거되었습니다)"
                        time.sleep(0.1) # DB 반영 대기
                        st.rerun()

                # 수정된 행 처리 (일괄 적용 버튼 클릭 시 실행)
                edited_rows = editor_state.get("edited_rows", {})
                
                # 버튼을 통해 일괄 적용
                col_btn_1, col_btn_2 = st.columns([8, 2])
                with col_btn_2:
                    apply_btn = st.button("✏️ 수정 사항 일괄 적용", key="apply_edits", disabled=not edited_rows, type="primary")

                if apply_btn and edited_rows:
                    # edited_rows는 {row_idx: {col_name: new_value}} 형태
                    
                    # 역방향 컬럼 매핑 (UI -> DB)
                    reverse_column_map = {v: k for k, v in column_map.items()}
                    
                    updated_count = 0
                    for row_idx, changes in edited_rows.items():
                        # 실제 ID 조회
                        row_id = int(df_dup.iloc[int(row_idx)]['id'])
                        
                        # 변경된 데이터 DB 컬럼명으로 변환
                        db_changes = {}
                        for ui_col, new_val in changes.items():
                            if ui_col in reverse_column_map:
                                db_col = reverse_column_map[ui_col]
                                db_changes[db_col] = new_val
                        
                        if db_changes:
                            MigrationService.update_transaction(row_id, db_changes)
                            updated_count += 1
                    
                    if updated_count > 0:
                        st.session_state['dup_msg'] = f"총 {updated_count}건 수정 완료."
                        time.sleep(0.1)
                        st.rerun()

    # (이전 로직 제거)
    # if not df_dup.empty: ...

    st.markdown("#### 🚨 위험 지역 (Danger Zone)")
    with st.expander("🗑️ 전체 데이터 삭제 (주의!)"):
        st.warning("⚠️ 이 작업은 되돌릴 수 없습니다. 모든 회계 데이터가 영구적으로 삭제됩니다.")
        if st.checkbox("데이터를 모두 삭제하는 것에 동의합니다.", key="agree_delete_all"):
            if st.button("🔥 전체 데이터 즉시 삭제", type="primary"):
                try:
                    MigrationService.delete_all_transactions()
                    st.success("모든 데이터가 삭제되었습니다.")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"삭제 중 오류 발생: {e}")

    # (이전 로직 제거)
    # if not df_dup.empty: ...

def _render_accounting_table():
    """회계 데이터 페이징 조회 테이블"""
    st.markdown("### 📋 저장된 데이터 확인")
    
    if 'acc_page' not in st.session_state:
        st.session_state['acc_page'] = 1
        
    # 데이터 건수 조회
    total_rows = MigrationService.get_accounting_summary()
    ROWS_PER_PAGE = 20
    
    if total_rows == 0:
        st.info("저장된 데이터가 없습니다.")
        return

    total_pages = math.ceil(total_rows / ROWS_PER_PAGE)
    
    # 페이지 보정
    if st.session_state['acc_page'] > total_pages: st.session_state['acc_page'] = total_pages
    if st.session_state['acc_page'] < 1: st.session_state['acc_page'] = 1
    
    current_page = st.session_state['acc_page']
    
    # 페이징 컨트롤 (TOP)
    col_l, col_r = st.columns([8, 2])
    with col_l:
        st.markdown(f"**Total: {total_rows}건**")
    with col_r:
        st.markdown(f"**Page {current_page} / {total_pages}**")

    # 데이터 조회
    df = MigrationService.get_accounting_data(limit=ROWS_PER_PAGE, offset=(current_page-1)*ROWS_PER_PAGE)
    
    # 컬럼 매핑 Display
    column_map = {
        'type': '수입/지출', 'gwan': '관', 'hang': '항', 'mok': '목', 'semok': '세목',
        'detail_1': '상세1', 'detail_2': '상세2', 'detail_3': '상세3', 'detail_4': '상세4',
        'amount': '금액', 'account_name': '계좌명', 'reg_date': '등기일'
    }
    
    st.dataframe(
        df.rename(columns=column_map),
        use_container_width=True,
        hide_index=True,
        column_config={
            "금액": st.column_config.NumberColumn(format="%d원")
        }
    )
    
    # 페이징 컨트롤 (Bottom)
    c1, c2, c3, c4, c5 = st.columns([1, 1, 4, 1, 1])
    with c2:
        if st.button("◀ 이전", key="acc_prev", disabled=(current_page <= 1)):
            st.session_state['acc_page'] -= 1
            st.rerun()
    with c4:
        if st.button("다음 ▶", key="acc_next", disabled=(current_page >= total_pages)):
            st.session_state['acc_page'] += 1
            st.rerun()
