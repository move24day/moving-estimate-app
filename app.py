# app.py (최종 버전: 모든 로직 분리 완료)
import streamlit as st
import pandas as pd
from datetime import datetime # timedelta 는 이제 calculations.py 에서 사용 안 함 (직접 사용 X)
import base64 # PDF 다운로드 링크 생성 시 필요
import math # ceil 사용 위함

# 분리된 모듈 불러오기
import data
import utils
import pdf_generator
import calculations # 새로 추가

# --- 페이지 설정 ---
st.set_page_config(page_title="이삿날 스마트견적", layout="wide")

# --- 타이틀 ---
st.title("🚚 이삿날 스마트견적")

# --- 데이터 정의 ---
# (data.py 로 이동됨)

# --- 함수 정의 ---
# (대부분 utils.py, pdf_generator.py, calculations.py 로 이동됨)
# (세션 초기화 함수는 여기에 남겨둠)

# --- 세션 상태 초기화 ---
def initialize_session_state():
    """세션 상태 변수들 초기화"""
    defaults = {
        "base_move_type": "가정 이사 🏠",
        "is_storage_move": False,
        "apply_long_distance": False,
        "final_box_count": 0,
        "final_basket_count": 0,
        "remove_base_housewife": False,
        "customer_name": "", "customer_phone": "", "from_location": "", "to_location": "",
        "moving_date": datetime.now().date(), "from_floor": "", "from_method": data.METHOD_OPTIONS[0], # data 사용
        "to_floor": "", "to_method": data.METHOD_OPTIONS[0], "special_notes": "", # data 사용
        "storage_duration": 1, "final_to_location": "", "final_to_floor": "", "final_to_method": data.METHOD_OPTIONS[0], # data 사용
        "long_distance_selector": data.long_distance_options[0], # data 사용
        "vehicle_select_radio": "자동 추천 차량 사용",
        "manual_vehicle_select_value": None,
        "final_selected_vehicle": None,
        "sky_hours_from": 2, "sky_hours_final": 2,
        "add_men": 0, "add_women": 0,
        "has_waste_check": False, "waste_tons_input": 0.5,
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False, "date_opt_3_widget": False,
        "total_volume": 0.0,
        "total_weight": 0.0,
        "recommended_vehicle_auto": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # 이사 유형 변경 시 해당 유형 품목 수량 초기화 (기존 로직 유지)
    current_move_type = st.session_state.base_move_type
    current_items_def = data.item_definitions.get(current_move_type, {}) # data 사용
    for section, item_list in current_items_def.items():
        for item in item_list:
            widget_key = f"qty_{current_move_type}_{section}_{item}"
            if widget_key not in st.session_state:
                st.session_state[widget_key] = 0

# --- 메인 애플리케이션 로직 ---
initialize_session_state() # 세션 초기화 함수 호출

current_move_type = st.session_state.base_move_type

# --- 탭 생성 ---
tab1, tab2, tab3 = st.tabs(["고객 정보", "물품 선택", "견적 및 비용"])

# --- 탭 1: 고객 정보 ---
with tab1:
    st.header("📝 고객 기본 정보")
    base_move_type_options = list(data.item_definitions.keys()) # data 사용
    st.radio(
        "🏢 기본 이사 유형:", base_move_type_options,
        index=base_move_type_options.index(current_move_type),
        horizontal=True, key="base_move_type"
    )
    col_check1, col_check2 = st.columns(2)
    with col_check1:
        st.checkbox("📦 보관이사 여부", key="is_storage_move")
    with col_check2:
        st.checkbox("🛣️ 장거리 이사 적용", key="apply_long_distance")

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("👤 고객명", key="customer_name")
        st.text_input("📍 출발지", key="from_location")
        st.date_input("🚚 이사일 (출발일)", key="moving_date")
        if st.session_state.apply_long_distance:
            current_long_distance_value = st.session_state.get("long_distance_selector", data.long_distance_options[0]) # data 사용
            current_index = data.long_distance_options.index(current_long_distance_value) if current_long_distance_value in data.long_distance_options else 0 # data 사용 (2곳)
            st.selectbox("🛣️ 장거리 구간 선택", data.long_distance_options, index=current_index, key="long_distance_selector") # data 사용
    with col2:
        st.text_input("📞 전화번호", key="customer_phone", placeholder="01012345678")
        to_location_label = "보관지" if st.session_state.is_storage_move else "도착지"
        st.text_input(f"📍 {to_location_label}", key="to_location")
        st.caption(f"⏱️ 견적일: {utils.get_current_kst_time_str()}") # utils 사용

    st.divider()
    st.header("🏢 작업 조건")
    col3, col4 = st.columns(2)
    with col3:
        st.text_input("🔼 출발지 층수", key="from_floor", placeholder="예: 3")
        from_method_index = data.METHOD_OPTIONS.index(st.session_state.from_method) if st.session_state.from_method in data.METHOD_OPTIONS else 0 # data 사용 (2곳)
        st.selectbox("🛗 출발지 작업 방법", data.METHOD_OPTIONS, index=from_method_index, key="from_method") # data 사용
    with col4:
        to_floor_label = "보관지 층수" if st.session_state.is_storage_move else "도착지 층수"
        to_method_label = "보관지 작업 방법" if st.session_state.is_storage_move else "도착지 작업 방법"
        st.text_input(f"{'🏢' if st.session_state.is_storage_move else '🔽'} {to_floor_label}", key="to_floor", placeholder="예: 5")
        to_method_index = data.METHOD_OPTIONS.index(st.session_state.to_method) if st.session_state.to_method in data.METHOD_OPTIONS else 0 # data 사용 (2곳)
        st.selectbox(f"🛠️ {to_method_label}", data.METHOD_OPTIONS, index=to_method_index, key="to_method") # data 사용

    if st.session_state.is_storage_move:
        st.divider()
        st.subheader("📦 보관이사 추가 정보")
        col5, col6 = st.columns(2)
        with col5:
            st.number_input("🗓️ 보관 기간 (일)", min_value=1, step=1, key="storage_duration")
            st.text_input("📍 최종 도착지 (입고지)", key="final_to_location")
        with col6:
            st.text_input("🔽 최종 도착지 층수 (입고지)", key="final_to_floor", placeholder="예: 10")
            final_to_method_index = data.METHOD_OPTIONS.index(st.session_state.final_to_method) if st.session_state.final_to_method in data.METHOD_OPTIONS else 0 # data 사용 (2곳)
            st.selectbox("🚚 최종 도착지 작업 방법 (입고지)", data.METHOD_OPTIONS, index=final_to_method_index, key="final_to_method") # data 사용
        st.info("보관이사는 기본 이사 비용(차량+인원)이 2배로 적용되며, 일일 보관료 및 최종 도착지 작업 비용이 추가됩니다.", icon="ℹ️")

    st.divider()
    st.header("🗒️ 특이 사항 입력")
    st.text_area("특이 사항이 있으면 입력해주세요.", height=100, key="special_notes")

# --- 탭 2: 물품 선택 ---
with tab2:
    st.header("📋 품목 선택")
    st.caption(f"현재 선택된 기본 이사 유형: **{current_move_type}**")

    # 계산 함수 호출 (calculations 모듈 사용)
    st.session_state.total_volume, st.session_state.total_weight = calculations.calculate_total_volume_weight(current_move_type)
    st.session_state.recommended_vehicle_auto, remaining_space = calculations.recommend_vehicle(st.session_state.total_volume, st.session_state.total_weight)

    item_category_to_display = data.item_definitions.get(current_move_type, {}) # data 사용
    for section, item_list in item_category_to_display.items():
        with st.expander(f"{section} 선택"):
            cols = st.columns(2)
            num_items = len(item_list)
            items_per_col = math.ceil(num_items / 2) if num_items > 0 else 1
            for idx, item in enumerate(item_list):
                col_index = idx // items_per_col
                if col_index < len(cols):
                    with cols[col_index]:
                        if item in data.items: # data 사용
                            unit = "칸" if item == "장롱" else "개"
                            widget_key = f"qty_{current_move_type}_{section}_{item}"
                            st.number_input(label=f"{item} ({unit})", min_value=0, step=1, key=widget_key)
                        else:
                            st.warning(f"'{item}' 품목 정보 없음")

    st.divider()
    st.subheader("📦 선택한 품목 정보 및 예상 물량")
    current_selection_display = {}
    for section, item_list_calc in item_category_to_display.items():
        for item_calc in item_list_calc:
            widget_key_calc = f"qty_{current_move_type}_{section}_{item_calc}"
            qty = st.session_state.get(widget_key_calc, 0)
            if qty > 0 and item_calc in data.items: # data 사용
                unit_calc = "칸" if item_calc == "장롱" else "개"
                current_selection_display[item_calc] = (qty, unit_calc)

    if current_selection_display:
        cols_disp = st.columns(2)
        item_list_disp = list(current_selection_display.items())
        items_per_col_disp = math.ceil(len(item_list_disp) / 2) if len(item_list_disp) > 0 else 1
        for i, (item_disp, (qty_disp, unit_disp)) in enumerate(item_list_disp):
            col_idx_disp = i // items_per_col_disp
            if col_idx_disp < 2:
                with cols_disp[col_idx_disp]: st.write(f"**{item_disp}**: {qty_disp} {unit_disp}")

        st.subheader("🚚 추천 차량 정보")
        st.info(f"📊 총 부피: {st.session_state.total_volume:.2f} m³ | 총 무게: {st.session_state.total_weight:.2f} kg")
        recommended_vehicle_display = st.session_state.recommended_vehicle_auto
        if recommended_vehicle_display and "초과" not in recommended_vehicle_display:
            st.success(f"🚛 추천 차량: **{recommended_vehicle_display}** ({remaining_space:.1f}% 여유)")
            spec = data.vehicle_specs.get(recommended_vehicle_display) # data 사용
            if spec:
                st.caption(f"({recommended_vehicle_display} 최대: {spec['capacity']}m³, {spec['weight_capacity']:,}kg)")
        elif recommended_vehicle_display and "초과" in recommended_vehicle_display:
             st.error(f"🚛 추천 차량: **{recommended_vehicle_display}**. 더 큰 차량 필요 또는 물량 조절 필요.")
        else:
            st.warning("🚛 추천 차량: 자동 추천 불가 (물량이 없거나 차량 정보 부족).")
    else:
        st.info("선택된 품목이 없습니다.")
        st.subheader("🚚 추천 차량 정보")
        st.info("📊 총 부피: 0.00 m³ | 총 무게: 0.00 kg")
        st.warning("🚛 추천 차량: 품목을 선택해주세요.")

# --- 탭 3: 견적 및 비용 ---
with tab3:
    st.header("💰 이사 비용 계산")
    is_storage = st.session_state.is_storage_move

    # --- 차량 선택 ---
    # (UI 로직은 app.py 에 남김)
    col_v1, col_v2 = st.columns([1, 2])
    with col_v1:
        st.radio(
            "차량 선택 방식:", ["자동 추천 차량 사용", "수동으로 차량 선택"],
            index=["자동 추천 차량 사용", "수동으로 차량 선택"].index(st.session_state.vehicle_select_radio),
            key="vehicle_select_radio"
        )

    selected_vehicle = None
    recommended_vehicle_auto = st.session_state.recommended_vehicle_auto
    vehicle_prices_options = data.vehicle_prices.get(current_move_type, {}) # data 사용
    available_trucks = sorted(vehicle_prices_options.keys(), key=lambda x: data.vehicle_specs.get(x, {}).get("capacity", 0)) # data 사용

    with col_v2:
        use_auto = st.session_state.vehicle_select_radio == "자동 추천 차량 사용"
        valid_auto_recommendation = recommended_vehicle_auto and "초과" not in recommended_vehicle_auto and recommended_vehicle_auto in available_trucks

        if use_auto:
            if valid_auto_recommendation:
                selected_vehicle = recommended_vehicle_auto
                st.success(f"자동 선택된 차량: **{selected_vehicle}**")
                spec = data.vehicle_specs.get(selected_vehicle) # data 사용
                if spec:
                    st.caption(f"({selected_vehicle} 최대: {spec['capacity']}m³, {spec['weight_capacity']:,}kg)")
                    st.caption(f"현재 물량: {st.session_state.total_volume:.2f} m³ ({st.session_state.total_weight:.2f} kg)")
            else:
                st.error(f"자동 추천 차량({recommended_vehicle_auto}) 사용 불가. 수동 선택 필요.")

        if not use_auto or (use_auto and not valid_auto_recommendation):
            if not available_trucks:
                st.error("선택 가능한 차량 정보가 없습니다.")
            else:
                default_manual_vehicle = st.session_state.manual_vehicle_select_value
                if default_manual_vehicle not in available_trucks:
                    if valid_auto_recommendation:
                        default_manual_vehicle = recommended_vehicle_auto
                    else:
                        default_manual_vehicle = available_trucks[0]

                current_manual_index = available_trucks.index(default_manual_vehicle) if default_manual_vehicle in available_trucks else 0

                selected_vehicle = st.selectbox("🚚 차량 선택 (수동):", available_trucks, index=current_manual_index, key="manual_vehicle_select_value")
                st.info(f"수동 선택 차량: **{selected_vehicle}**")
                spec = data.vehicle_specs.get(selected_vehicle) # data 사용
                if spec:
                    st.caption(f"({selected_vehicle} 최대: {spec['capacity']}m³, {spec['weight_capacity']:,}kg)")
                    st.caption(f"현재 물량: {st.session_state.total_volume:.2f} m³ ({st.session_state.total_weight:.2f} kg)")

    # 최종 선택된 차량 및 박스/바구니 수량 업데이트
    st.session_state.final_selected_vehicle = selected_vehicle
    if selected_vehicle:
        st.session_state.final_box_count, st.session_state.final_basket_count = calculations.calculate_boxes_baskets(selected_vehicle) # calculations 사용
    else:
        st.session_state.final_box_count, st.session_state.final_basket_count = 0, 0

    # --- 기타 옵션 UI ---
    # (UI 로직은 app.py 에 남김)
    st.divider()
    st.subheader("🛠️ 작업 및 추가 옵션")

    uses_sky_from = st.session_state.get('from_method') == "스카이 🏗️"
    final_dest_method_key = 'final_to_method' if is_storage else 'to_method'
    uses_sky_final_to = st.session_state.get(final_dest_method_key) == "스카이 🏗️"
    if uses_sky_from or uses_sky_final_to:
        st.warning("스카이 작업 포함됨. 필요시 시간 조절.", icon="🏗️")
        col_sky1, col_sky2 = st.columns(2)
        if uses_sky_from:
            with col_sky1: st.number_input("출발지 스카이 시간 (기본 2시간)", min_value=2, step=1, key="sky_hours_from")
        if uses_sky_final_to:
            to_label = "최종 도착지" if is_storage else "도착지"
            with col_sky2: st.number_input(f"{to_label} 스카이 시간 (기본 2시간)", min_value=2, step=1, key="sky_hours_final")

    col_add1, col_add2 = st.columns(2)
    with col_add1:
        st.number_input("추가 남성 인원 👨", min_value=0, step=1, key="add_men")
    with col_add2:
        st.number_input("추가 여성 인원 👩", min_value=0, step=1, key="add_women")

    base_women_count = 0
    show_remove_option = False
    if current_move_type == "가정 이사 🏠" and selected_vehicle:
        base_info_for_check = data.vehicle_prices.get(current_move_type, {}).get(selected_vehicle, {}) # data 사용
        base_women_count = base_info_for_check.get('housewife', 0)
        if base_women_count > 0:
            show_remove_option = True

    if show_remove_option:
        st.checkbox(f"기본 여성 인원({base_women_count}명) 제외하고 할인 적용 👩‍🔧 (-{data.ADDITIONAL_PERSON_COST:,}원)", key="remove_base_housewife") # data 사용
    else:
        if st.session_state.remove_base_housewife:
             st.session_state.remove_base_housewife = False # 상태 초기화는 UI 로직상 여기에 두는 것이 적절할 수 있음

    col_waste1, col_waste2 = st.columns(2)
    with col_waste1:
        st.checkbox("폐기물 처리 필요 🗑️", key="has_waste_check")
    with col_waste2:
        if st.session_state.has_waste_check:
            st.number_input("폐기물 양 (톤)", min_value=0.5, max_value=10.0, step=0.5, key="waste_tons_input")
            st.caption(f"💡 1톤당 {data.WASTE_DISPOSAL_COST_PER_TON:,}원 추가") # data 사용

    st.subheader("📅 날짜 유형 선택 (중복 가능, 해당 시 할증)")
    date_options = ["이사많은날 🏠", "손없는날 ✋", "월말 📅", "공휴일 🎉"]
    # selected_dates 는 calculations 에서 계산하므로 여기서는 UI 만 그림
    cols_date = st.columns(4)
    date_keys = ["date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget", "date_opt_3_widget"]
    for i, option in enumerate(date_options):
        cols_date[i].checkbox(option, key=date_keys[i])

    # --- 비용 계산 및 표시 ---
    st.divider()
    st.subheader("💵 이사 비용 계산")

    # 계산 함수 호출 (calculations 모듈 사용)
    # st.session_state 전체를 딕셔너리로 변환하여 전달
    total_cost, calculated_cost_items = calculations.calculate_total_moving_cost(st.session_state.to_dict())

    # 계산 결과 표시 (UI 로직)
    if selected_vehicle: # 차량이 선택되었을 때만 결과 표시
        st.subheader("📊 비용 상세 내역")
        if calculated_cost_items:
            cost_df = pd.DataFrame(calculated_cost_items, columns=["항목", "금액", "비고"])
            st.dataframe(cost_df.style.format({"금액": "{}"}).set_properties(**{'text-align': 'right'}, subset=['금액']), use_container_width=True)
        else:
            # 비용 계산 함수가 빈 리스트를 반환한 경우 (예: 오류 또는 계산 항목 없음)
            st.info("계산된 비용 항목이 없습니다.")

        st.subheader(f"💰 총 견적 비용: {total_cost:,.0f}원")

        # 특이사항 표시는 여기에 남김
        if st.session_state.special_notes:
            st.subheader("📝 특이 사항")
            st.info(st.session_state.special_notes)
    else:
        # 차량 미선택 시 메시지
        st.warning("차량을 먼저 선택해주세요.")

    # --- PDF 견적서 생성 기능 ---
    # (UI 및 호출 로직은 app.py 에 남김)
    st.divider()
    st.subheader("📄 견적서 다운로드")
    can_generate_pdf = selected_vehicle and (st.session_state.customer_name or st.session_state.customer_phone)

    if st.button("PDF 견적서 생성", disabled=not can_generate_pdf, key="pdf_generate_button"):
        if not selected_vehicle:
            st.error("PDF 생성을 위해 차량을 선택해주세요.")
        elif not (st.session_state.customer_name or st.session_state.customer_phone):
            st.error("PDF 생성을 위해 고객명 또는 전화번호를 입력해주세요.")
        else:
            # PDF 생성 함수 호출 (pdf_generator 모듈 사용)
            pdf_data = pdf_generator.generate_pdf(st.session_state.to_dict(), calculated_cost_items, total_cost)

            if pdf_data:
                b64_pdf = base64.b64encode(pdf_data).decode("utf-8")
                # 전화번호 추출 함수 호출 (utils 모듈 사용)
                phone_part = utils.extract_phone_number_part(st.session_state.customer_phone)
                file_prefix = "보관이사견적서" if is_storage else "이사견적서"
                file_name = f"{file_prefix}_{phone_part}_{datetime.now().strftime('%Y%m%d')}.pdf"
                href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{file_name}">📥 {file_prefix} 다운로드 ({file_name})</a>'
                st.markdown(href, unsafe_allow_html=True)

    elif not can_generate_pdf:
        st.caption("PDF를 생성하려면 고객명/전화번호 입력 및 차량 선택이 필요합니다.")
