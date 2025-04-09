import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import base64
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 페이지 설정
st.set_page_config(page_title="이삿날 스마트견적", layout="wide")

# 타이틀 표시 (로고 대체)
st.title("🚚 이삿날 스마트견적")

# --- (기존 데이터 정의: office_vehicle_prices, home_vehicle_prices, ladder_prices, special_day_prices, etc.) ---
# (이 부분은 변경 없음)
# 차량 톤수와 유형에 따른 기본 비용
office_vehicle_prices = {
    "1톤": {"price": 400000, "men": 2},
    "2.5톤": {"price": 650000, "men": 2},
    "3.5톤": {"price": 700000, "men": 2},
    "5톤": {"price": 950000, "men": 3},
    "6톤": {"price": 1050000, "men": 3},
    "7.5톤": {"price": 1300000, "men": 4},
    "10톤": {"price": 1700000, "men": 5},
    "15톤": {"price": 2000000, "men": 6},
    "20톤": {"price": 2500000, "men": 8},
}

home_vehicle_prices = {
    "1톤": {"price": 400000, "men": 2, "housewife": 0},
    "2.5톤": {"price": 900000, "men": 2, "housewife": 1},
    "3.5톤": {"price": 950000, "men": 2, "housewife": 1},
    "5톤": {"price": 1200000, "men": 3, "housewife": 1},
    "6톤": {"price": 1350000, "men": 3, "housewife": 1},
    "7.5톤": {"price": 1750000, "men": 4, "housewife": 1},
    "10톤": {"price": 2300000, "men": 5, "housewife": 1},
    "15톤": {"price": 2800000, "men": 6, "housewife": 1},
    "20톤": {"price": 3500000, "men": 8, "housewife": 1},
}

# 사다리 비용 (층수와 톤수에 따른)
ladder_prices = {
    "2~5층": {"5톤": 150000, "6톤": 180000, "7.5톤": 210000, "10톤": 240000},
    "6~7층": {"5톤": 160000, "6톤": 190000, "7.5톤": 220000, "10톤": 250000},
    "8~9층": {"5톤": 170000, "6톤": 200000, "7.5톤": 230000, "10톤": 260000},
    "10~11층": {"5톤": 180000, "6톤": 210000, "7.5톤": 240000, "10톤": 270000},
    "12~13층": {"5톤": 190000, "6톤": 220000, "7.5톤": 250000, "10톤": 280000},
    "14층": {"5톤": 200000, "6톤": 230000, "7.5톤": 260000, "10톤": 290000},
    "15층": {"5톤": 210000, "6톤": 240000, "7.5톤": 270000, "10톤": 300000},
    "16층": {"5톤": 220000, "6톤": 250000, "7.5톤": 280000, "10톤": 310000},
    "17층": {"5톤": 230000, "6톤": 260000, "7.5톤": 290000, "10톤": 320000},
    "18층": {"5톤": 250000, "6톤": 280000, "7.5톤": 310000, "10톤": 340000},
    "19층": {"5톤": 260000, "6톤": 290000, "7.5톤": 320000, "10톤": 350000},
    "20층": {"5톤": 280000, "6톤": 310000, "7.5톤": 340000, "10톤": 370000},
    "21층": {"5톤": 310000, "6톤": 340000, "7.5톤": 370000, "10톤": 400000},
    "22층": {"5톤": 340000, "6톤": 370000, "7.5톤": 400000, "10톤": 430000},
    "23층": {"5톤": 370000, "6톤": 400000, "7.5톤": 430000, "10톤": 460000},
    "24층": {"5톤": 400000, "6톤": 430000, "7.5톤": 460000, "10톤": 490000},
}

special_day_prices = {
    "평일(일반)": 0,
    "이사많은날 🏠": 200000,
    "손없는날 ✋": 100000,
    "월말 📅": 100000,
    "공휴일 🎉": 100000,
}

# 추가 인원 비용
additional_person_cost = 200000 # 추가 인원 1명당 20만원

# 폐기물 처리 비용
waste_disposal_cost = 300000 # 폐기물 1톤당 30만원

# 스카이 비용
sky_base_price = 300000 # 기본 2시간
sky_extra_hour_price = 50000 # 추가 시간당

# 품목 데이터 (부피 m³, 무게 kg)
items = {
    "방": {
        "장롱": (1.05, 120.0), "싱글침대": (1.20, 60.0), "더블침대": (1.70, 70.0), "돌침대": (2.50, 150.0),
        "옷장": (1.05, 160.0), "서랍장(3단)": (0.40, 30.0), "서랍장(5단)": (0.75, 40.0), "화장대": (0.32, 80.0),
        "중역책상": (1.20, 80.0), "책장": (0.96, 56.0), "책상&의자": (0.25, 40.0), "옷행거": (0.35, 40.0),
    },
    "거실": {
        "소파(1인용)": (0.40, 30.0), "소파(3인용)": (0.60, 50.0), "소파 테이블": (0.65, 35.0),
        "TV(45인치)": (0.15, 15.0), "TV(75인치)": (0.30, 30.0), "장식장": (0.75, 40.0),
        "오디오 및 스피커": (0.10, 20.0), "에어컨": (0.15, 30.0), "피아노(일반)": (1.50, 200.0),
        "피아노(디지털)": (0.50, 50.0), "안마기": (0.90, 50.0), "공기청정기": (0.10, 8.0),
    },
    "주방": {
        "양문형 냉장고": (1.00, 120.0), "4도어 냉장고": (1.20, 130.0), "김치냉장고(스탠드형)": (0.80, 90.0),
        "김치냉장고(일반형)": (0.60, 60.0), "식탁(4인)": (0.40, 50.0), "식탁(6인)": (0.60, 70.0),
        "가스레인지 및 인덕션": (0.10, 10.0), "주방용 선반(수납장)": (1.10, 80.0),
    },
    "기타": {
        "세탁기 및 건조기": (0.50, 80.0), "신발장": (1.10, 60.0), "여행가방 및 캐리어": (0.15, 5.0),
        "화분": (0.20, 10.0), "스타일러스": (0.50, 20.0),
    },
}

# 차량 부피 용량 정보 (m³)
vehicle_capacity = {
    "1톤": 5, "2.5톤": 12, "3.5톤": 18, "5톤": 25, "6톤": 30,
    "7.5톤": 40, "10톤": 50, "15톤": 70, "20톤": 90,
}

# 차량 무게 용량 정보 (kg)
vehicle_weight_capacity = {
    "1톤": 1000, "2.5톤": 2500, "3.5톤": 3500, "5톤": 5000, "6톤": 6000,
    "7.5톤": 7500, "10톤": 10000, "15톤": 15000, "20톤": 20000,
}


# --- (기존 함수 정의: recommend_vehicle, get_ladder_range) ---
# (이 부분은 변경 없음)
# 차량 추천 함수
def recommend_vehicle(total_volume, total_weight):
    loading_efficiency = 0.90 # 적재 효율 90%

    # 부피 기준 오름차순 정렬된 차량 이름 리스트
    sorted_vehicles_by_capacity = sorted(vehicle_capacity.keys(), key=lambda x: vehicle_capacity[x])

    for name in sorted_vehicles_by_capacity:
        # 딕셔너리에 키가 있는지 확인 후 접근
        if name in vehicle_capacity and name in vehicle_weight_capacity:
            effective_capacity = vehicle_capacity[name] * loading_efficiency
            # 총 부피와 총 무게가 차량의 유효 용량 및 무게 용량 이하인지 확인
            if total_volume <= effective_capacity and total_weight <= vehicle_weight_capacity[name]:
                remaining_space = (
                    (effective_capacity - total_volume) / effective_capacity * 100
                    if effective_capacity > 0 else 0 # 0으로 나누는 경우 방지
                )
                return name, remaining_space
        else:
            # 이론상 발생하면 안 되지만, 데이터 오류 방지
            print(f"Warning: Vehicle data missing for {name}")

    # 모든 차량 용량을 초과하는 경우
    # 가장 큰 차량 정보 반환 시도 (또는 특정 메시지)
    largest_vehicle = sorted_vehicles_by_capacity[-1] if sorted_vehicles_by_capacity else None
    if largest_vehicle:
        return f"{largest_vehicle} 초과", 0 # 또는 다른 적절한 메시지
    else:
        return "차량 정보 없음", 0


# 층수에 따른 사다리 세부 구간 매핑 함수
def get_ladder_range(floor):
    try:
        floor_num = int(floor)
        if floor_num < 2:
            return None # 1층 이하는 사다리 필요 없음
        elif 2 <= floor_num <= 5: return "2~5층"
        elif 6 <= floor_num <= 7: return "6~7층"
        elif 8 <= floor_num <= 9: return "8~9층"
        elif 10 <= floor_num <= 11: return "10~11층"
        elif 12 <= floor_num <= 13: return "12~13층"
        elif floor_num == 14: return "14층"
        elif floor_num == 15: return "15층"
        elif floor_num == 16: return "16층"
        elif floor_num == 17: return "17층"
        elif floor_num == 18: return "18층"
        elif floor_num == 19: return "19층"
        elif floor_num == 20: return "20층"
        elif floor_num == 21: return "21층"
        elif floor_num == 22: return "22층"
        elif floor_num == 23: return "23층"
        elif floor_num >= 24: return "24층"
    except (ValueError, TypeError): # 숫자가 아니거나 None인 경우 등 처리
        return None # 숫자로 변환할 수 없는 경우

    return None

# --- (세션 상태 초기화) ---
if "selected_items" not in st.session_state:
    st.session_state.selected_items = {}
if "additional_boxes" not in st.session_state:
    st.session_state.additional_boxes = {"중대박스": 0, "옷박스": 0, "중박스": 0}
if "move_type" not in st.session_state:
    st.session_state.move_type = "가정 이사 🏠"
# Session state for inputs if not already set (avoids errors on first run/refresh)
default_values = {
    "customer_name": "", "customer_phone": "", "from_location": "", "to_location": "",
    "moving_date": datetime.now().date(), "from_floor": "", "from_method": "사다리차",
    "to_floor": "", "to_method": "사다리차", "special_notes": ""
}
for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- (탭 생성 및 탭 1: 고객 정보) ---
tab1, tab2, tab3 = st.tabs(["고객 정보", "물품 선택", "견적 및 비용"])

with tab1:
    st.header("📝 고객 기본 정보")
    move_type_options = ["가정 이사 🏠", "사무실 이사 🏢"]
    st.session_state.move_type = st.radio(
        "🏢 이사 유형 선택:", move_type_options, horizontal=True, key="move_type_radio" # Give unique key if needed elsewhere
    )

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("👤 고객명", key="customer_name")
        st.text_input("📍 출발지", key="from_location")
    with col2:
        st.text_input("📞 전화번호", key="customer_phone", placeholder="01012345678")
        st.text_input("📍 도착지", key="to_location")

    st.date_input("🚚 이사일", key="moving_date")

    # 견적일 자동 표시 (현재시간) - Define it here so it's available later
    try:
        kst = pytz.timezone("Asia/Seoul")
        estimate_date = datetime.now(kst).strftime("%Y-%m-%d %H:%M")
    except pytz.UnknownTimeZoneError:
        estimate_date = datetime.now().strftime("%Y-%m-%d %H:%M") # Fallback
        st.warning("Asia/Seoul 타임존을 찾을 수 없어 현재 시스템 시간으로 견적일을 표시합니다.")


    st.header("🏢 작업 조건")
    col1, col2 = st.columns(2)
    method_options = ["사다리차", "승강기", "계단", "스카이"]
    with col1:
        st.text_input("🔼 출발지 층수", key="from_floor", placeholder="예: 3")
        st.selectbox("🛗 출발지 작업 방법", method_options, key="from_method")
    with col2:
        st.text_input("🔽 도착지 층수", key="to_floor", placeholder="예: 5")
        st.selectbox("🛗 도착지 작업 방법", method_options, key="to_method")

    st.header("🗒️ 특이 사항 입력")
    st.text_area("특이 사항이 있으면 입력해주세요.", height=100, key="special_notes")


# --- (탭 2: 물품 선택) ---
with tab2:
    st.header("📋 품목 선택")

    # Use temporary dicts within the tab scope for selection
    current_selection = {}
    current_boxes = {"중대박스": 0, "옷박스": 0, "중박스": 0}

    home_items = { "가정품목": { ... }, "기타품목": { ... } } # Keep your item definitions
    office_items = { "사무실품목": { ... }, "기타품목": { ... } } # Keep your item definitions
    # (위에 정의된 home_items, office_items 내용 그대로 사용)
    home_items = {
        "가정품목": {
            "장롱": items["방"]["장롱"], "더블침대": items["방"]["더블침대"], "서랍장(5단)": items["방"]["서랍장(5단)"],
            "화장대": items["방"]["화장대"], "TV(75인치)": items["거실"]["TV(75인치)"], "책상&의자": items["방"]["책상&의자"],
            "책장": items["방"]["책장"], "옷행거": items["방"]["옷행거"], "소파(3인용)": items["거실"]["소파(3인용)"],
            "장식장": items["거실"]["장식장"], "에어컨": items["거실"]["에어컨"], "4도어 냉장고": items["주방"]["4도어 냉장고"],
            "김치냉장고(스탠드형)": items["주방"]["김치냉장고(스탠드형)"], "식탁(4인)": items["주방"]["식탁(4인)"],
            "주방용 선반(수납장)": items["주방"]["주방용 선반(수납장)"], "세탁기 및 건조기": items["기타"]["세탁기 및 건조기"],
        },
        "기타품목": {
            "피아노(일반)": items["거실"]["피아노(일반)"], "피아노(디지털)": items["거실"]["피아노(디지털)"],
            "안마기": items["거실"]["안마기"], "스타일러스": items["기타"]["스타일러스"], "신발장": items["기타"]["신발장"],
            "화분": items["기타"]["화분"], "여행가방 및 캐리어": items["기타"]["여행가방 및 캐리어"],
        },
    }

    office_items = {
        "사무실품목": {
             "중역책상": items["방"]["중역책상"], "책상&의자": items["방"]["책상&의자"], "서랍장(5단)": items["방"]["서랍장(5단)"],
             "4도어 냉장고": items["주방"]["4도어 냉장고"], "TV(75인치)": items["거실"]["TV(75인치)"], "장식장": items["거실"]["장식장"],
             "에어컨": items["거실"]["에어컨"], "오디오 및 스피커": items["거실"]["오디오 및 스피커"],
        },
        "기타품목": {
             "안마기": items["거실"]["안마기"], "공기청정기": items["거실"]["공기청정기"], "화분": items["기타"]["화분"],
             "스타일러스": items["기타"]["스타일러스"], "신발장": items["기타"]["신발장"],
        },
    }


    item_category = home_items if st.session_state.move_type == "가정 이사 🏠" else office_items

    for section, item_list in item_category.items():
        with st.expander(f"{section} 선택"):
            cols = st.columns(3)
            items_list = list(item_list.items())
            # Calculate items per column robustly
            num_items = len(items_list)
            items_per_col = (num_items + 2) // 3 # Ensure distribution across 3 cols

            for idx, (item, (volume, weight)) in enumerate(items_list):
                col_index = idx // items_per_col
                with cols[col_index]:
                    unit = "칸" if item == "장롱" else "개"
                    # Use session state value as default for the number_input
                    default_qty = st.session_state.selected_items.get(item, (0,))[0]
                    qty = st.number_input(
                        f"{item}", min_value=0, step=1,
                        key=f"{section}_{item}", # Unique key for widget
                        value=default_qty # Set default value from session state
                    )
                    if qty > 0:
                        current_selection[item] = (qty, unit, volume, weight)
                        # 박스 자동 추가 조건 (가정 이사만 적용)
                        if st.session_state.move_type == "가정 이사 🏠":
                            if item == "장롱": current_boxes["중대박스"] += qty * 5
                            if item == "옷장": current_boxes["옷박스"] += qty * 3 # Note: 옷장 is not in default home_items list
                            if item == "서랍장(5단)": current_boxes["중박스"] += qty * 5
                    elif item in current_selection: # Remove if qty becomes 0
                         del current_selection[item]


    # Update session state *after* processing all inputs in the tab
    st.session_state.selected_items = current_selection
    st.session_state.additional_boxes = current_boxes

    # Recalculate totals based on updated session state
    box_volumes = {"중대박스": 0.1875, "옷박스": 0.219, "중박스": 0.1}
    total_volume = sum(
        qty * vol for item, (qty, unit, vol, weight) in st.session_state.selected_items.items()
    )
    total_volume += sum(
        box_volumes[box] * count for box, count in st.session_state.additional_boxes.items()
    )
    total_weight = sum(
        qty * weight for item, (qty, unit, vol, weight) in st.session_state.selected_items.items()
    )

    # --- (선택 품목 정보 및 추천 차량 표시 - 이 부분은 변경 없음) ---
    st.subheader("📦 선택한 품목 정보")
    if st.session_state.selected_items:
        cols = st.columns(3)
        item_list_display = list(st.session_state.selected_items.items())
        items_per_column_display = (len(item_list_display) + 2) // 3
        for i, (item, (qty, unit, vol, weight)) in enumerate(item_list_display):
             col_index = i // items_per_column_display
             if col_index < 3:
                 with cols[col_index]:
                     st.write(f"**{item}**: {qty} {unit}")

        # 실시간 차량 추천 정보 표시
        st.subheader("🚚 추천 차량 정보")
        # Make sure calculation happens before display
        recommended_vehicle, remaining_space = recommend_vehicle(total_volume, total_weight)
        st.info(f"📊 총 부피: {total_volume:.2f} m³ | 총 무게: {total_weight:.2f} kg")

        # Check if recommended_vehicle is valid before accessing dictionaries
        if recommended_vehicle != "차량 정보 없음" and "초과" not in recommended_vehicle:
             st.success(f"🚛 추천 차량: {recommended_vehicle} (여유 공간: {remaining_space:.2f}%)")
             # 차량 용량 정보 제공
             if recommended_vehicle in vehicle_capacity and recommended_vehicle in vehicle_weight_capacity:
                  st.markdown(f"""
                  **{recommended_vehicle} 정보**:
                  - 최대 적재 부피: {vehicle_capacity[recommended_vehicle]} m³
                  - 최대 적재 무게: {vehicle_weight_capacity[recommended_vehicle]} kg
                  """)
             else:
                  st.warning(f"{recommended_vehicle} 차량의 상세 용량 정보를 찾을 수 없습니다.")
        else:
            st.error(f"🚛 추천 차량: {recommended_vehicle}") # Show error/message if no suitable vehicle


    else:
        st.info("선택된 품목이 없습니다.")
        recommended_vehicle = "1톤" # Default or smallest vehicle if nothing selected
        remaining_space = 100.0
        st.subheader("🚚 추천 차량 정보")
        st.info("📊 총 부피: 0.00 m³ | 총 무게: 0.00 kg")
        st.warning("🚛 추천 차량: 품목을 선택해주세요.")



# --- (탭 3: 견적 및 비용) ---
with tab3:
    st.header("💰 이사 비용 계산")

    # Ensure recommend_vehicle is called if needed (might need recalculation here if tab 2 wasn't visited)
    # This calculation might be redundant if tab 2 was just visited, but safer
    current_total_volume = sum(qty * vol for item, (qty, unit, vol, weight) in st.session_state.selected_items.items()) \
                         + sum(box_volumes[box] * count for box, count in st.session_state.additional_boxes.items())
    current_total_weight = sum(qty * weight for item, (qty, unit, vol, weight) in st.session_state.selected_items.items())
    # Get recommended vehicle based on current items in session state
    tab3_recommended_vehicle, tab3_remaining_space = recommend_vehicle(current_total_volume, current_total_weight)


    col1, col2 = st.columns(2)
    with col1:
        vehicle_selection_option = st.radio(
            "차량 선택 방식:",
            ["자동 추천 차량 사용", "수동으로 차량 선택"],
            horizontal=True, key="vehicle_select_radio"
        )

    with col2:
        # Define selected_vehicle within this scope based on radio choice
        if vehicle_selection_option == "자동 추천 차량 사용":
            # Check if a valid recommendation exists
            if tab3_recommended_vehicle != "차량 정보 없음" and "초과" not in tab3_recommended_vehicle:
                selected_vehicle = tab3_recommended_vehicle
                st.success(f"추천 차량: {selected_vehicle} (여유 공간: {tab3_remaining_space:.2f}%)")
            else:
                 # Handle case where auto-recommendation failed
                 st.error(f"자동 추천 실패: {tab3_recommended_vehicle}. 수동으로 선택해주세요.")
                 # Default to smallest or force manual selection
                 vehicle_selection_option = "수동으로 차량 선택" # Force manual if auto fails
                 selected_vehicle = st.selectbox(
                     "🚚 차량 톤수 선택:", sorted(list(home_vehicle_prices.keys())), key="manual_vehicle_select_fallback"
                 )
        # This else covers both "수동으로 차량 선택" initially and the fallback case
        if vehicle_selection_option == "수동으로 차량 선택":
             # Ensure keys are consistent (home vs office) - Use home_vehicle_prices as the superset for selection range
             available_trucks = sorted(list(home_vehicle_prices.keys()))
             selected_vehicle = st.selectbox(
                 "🚚 차량 톤수 선택:", available_trucks, key="manual_vehicle_select"
             )

    # --- (사다리차/스카이/추가인원/폐기물/날짜 옵션 - 이 부분은 변경 없음) ---
    # Ensure these use st.session_state values correctly
    uses_ladder_from = st.session_state.get('from_method') == "사다리차"
    uses_ladder_to = st.session_state.get('to_method') == "사다리차"
    ladder_from_floor_range = get_ladder_range(st.session_state.get('from_floor'))
    ladder_to_floor_range = get_ladder_range(st.session_state.get('to_floor'))

    sky_hours = 2
    uses_sky = "스카이" in [st.session_state.get('from_method'), st.session_state.get('to_method')]
    if uses_sky:
        sky_hours = st.number_input("스카이 사용 시간 (기본 2시간 포함) ⏱️", min_value=2, step=1, value=2, key="sky_hours_input")

    st.subheader("👥 인원 추가 옵션")
    col1, col2 = st.columns(2)
    with col1: additional_men = st.number_input("추가 남성 인원 👨", min_value=0, step=1, key="add_men")
    with col2: additional_women = st.number_input("추가 여성 인원 👩", min_value=0, step=1, key="add_women")

    st.subheader("🗑️ 폐기물 처리 옵션")
    col1, col2 = st.columns(2)
    with col1: has_waste = st.checkbox("폐기물 처리 필요", key="has_waste_check")
    with col2:
        waste_tons = 0
        if has_waste:
            waste_tons = st.number_input("폐기물 양 (톤)", min_value=0.5, max_value=10.0, value=1.0, step=0.5, key="waste_tons_input")
            st.info("💡 폐기물 처리 비용: 1톤당 30만원이 추가됩니다.")

    st.subheader("📅 날짜 유형 선택 (중복 가능)")
    date_options = ["이사많은날 🏠", "손없는날 ✋", "월말 📅", "공휴일 🎉"]
    selected_dates = []
    col1, col2 = st.columns(2)
    # Use unique keys for checkboxes
    with col1:
        if st.checkbox(date_options[0], key="date_opt_0"): selected_dates.append(date_options[0])
        if st.checkbox(date_options[2], key="date_opt_2"): selected_dates.append(date_options[2])
    with col2:
        if st.checkbox(date_options[1], key="date_opt_1"): selected_dates.append(date_options[1])
        if st.checkbox(date_options[3], key="date_opt_3"): selected_dates.append(date_options[3])

    if not selected_dates:
        selected_dates_display = ["평일(일반)"] # For display and calculation logic
        special_day_cost_factor = 0 # Represents the cost for 평일
    else:
        selected_dates_display = selected_dates # Keep the selected ones
        # Calculate cost factor based on actual selections
        special_day_cost_factor = sum(special_day_prices.get(date, 0) for date in selected_dates)

    # --- (실시간 비용 계산 - 이 부분 대부분 변경 없음, selected_vehicle 사용 확인) ---
    # 기본 비용 설정 (selected_vehicle 사용)
    if st.session_state.move_type == "가정 이사 🏠":
        base_info = home_vehicle_prices.get(selected_vehicle, {"price": 0, "men": 0, "housewife": 0})
    else: # 사무실 이사
        base_info = office_vehicle_prices.get(selected_vehicle, {"price": 0, "men": 0})
        base_info["housewife"] = 0 # Ensure housewife key exists for consistency later if needed

    base_cost = base_info.get("price", 0) # Use .get for safety
    total_cost = base_cost

    # 사다리 비용 계산
    ladder_from_cost = ladder_to_cost = 0
    # Determine ladder vehicle size (use 5-ton price for smaller trucks)
    ladder_vehicle_size = "5톤"
    if selected_vehicle in ["5톤", "6톤", "7.5톤", "10톤"]:
         ladder_vehicle_size = selected_vehicle
    # Need to check existence of keys progressively
    if uses_ladder_from and ladder_from_floor_range:
        if ladder_from_floor_range in ladder_prices and ladder_vehicle_size in ladder_prices[ladder_from_floor_range]:
             ladder_from_cost = ladder_prices[ladder_from_floor_range][ladder_vehicle_size]
             total_cost += ladder_from_cost
    if uses_ladder_to and ladder_to_floor_range:
        if ladder_to_floor_range in ladder_prices and ladder_vehicle_size in ladder_prices[ladder_to_floor_range]:
             ladder_to_cost = ladder_prices[ladder_to_floor_range][ladder_vehicle_size]
             total_cost += ladder_to_cost


    # 스카이 비용 계산
    sky_cost = 0
    if uses_sky:
        sky_cost = sky_base_price + max(0, sky_hours - 2) * sky_extra_hour_price
        total_cost += sky_cost

    # 추가 인원 비용 계산
    additional_person_total = (additional_men + additional_women) * additional_person_cost
    total_cost += additional_person_total

    # 폐기물 처리 비용 계산
    waste_cost = waste_tons * waste_disposal_cost if has_waste else 0
    total_cost += waste_cost

    # 특별 날짜 비용 계산 (Use the pre-calculated sum)
    total_cost += special_day_cost_factor


    # --- (실시간 비용 세부 내역 표시 - 이 부분 변경 없음) ---
    st.subheader("💵 실시간 이사 비용 세부 내역")
    cost_items = [
        ["기본 이사 비용", f"{base_cost:,}원"],
        (["출발지 사다리차 비용", f"{ladder_from_cost:,}원"] if ladder_from_cost > 0 else None),
        (["도착지 사다리차 비용", f"{ladder_to_cost:,}원"] if ladder_to_cost > 0 else None),
        (["스카이 비용", f"{sky_cost:,}원 ({sky_hours}시간 사용)" ] if sky_cost > 0 else None), # Simplified text
        (["추가 인원 비용", f"{additional_person_total:,}원 ({additional_men + additional_women}명)"] if additional_person_total > 0 else None),
        (["폐기물 처리 비용", f"{waste_cost:,}원 ({waste_tons}톤)"] if waste_cost > 0 else None),
        (["이사 집중일 부담금", f"{special_day_cost_factor:,}원 ({', '.join(selected_dates_display)})"] if special_day_cost_factor > 0 else None),
    ]
    cost_items = [item for item in cost_items if item is not None] # Filter out None items
    cost_df = pd.DataFrame(cost_items, columns=["항목", "금액"])
    st.table(cost_df)

    st.subheader(f"💰 총 견적 비용: {total_cost:,}원")

    if st.session_state.get("special_notes", ""):
        st.subheader("📝 특이 사항")
        st.info(st.session_state.get("special_notes", ""))

    # --- (PDF 견적서 생성 기능 - 수정된 부분) ---
    st.subheader("📄 견적서 다운로드")
    if st.button("PDF 견적서 생성"):
        # Check if essential info is present before generating PDF
        if not st.session_state.get("customer_name"):
            st.error("PDF 생성을 위해 고객명을 입력해주세요.")
        elif not selected_vehicle: # Check if a vehicle was actually selected/determined
            st.error("PDF 생성을 위해 차량을 선택(또는 자동 추천)해주세요.")
        else:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)

            # 한글 폰트 경로 설정 (환경에 맞게 수정 필요)
            # 예: 로컬 / Streamlit Cloud 등
            font_path = "NanumGothic.ttf" # 기본 경로 (파일이 같은 폴더에 있다고 가정)
            # Streamlit Cloud 등에서는 절대 경로 또는 상대 경로 확인 필요
            if "RUNNING_ON_STREAMLIT_CLOUD" in os.environ:
                font_path = "/app/NanumGothic.ttf"  # Streamlit Cloud 경로 예시
            elif os.path.exists("./NanumGothic.ttf"):
                font_path = "./NanumGothic.ttf"

            font_registered = False
            try:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
                    font_registered = True
                else:
                    st.error(f"폰트 파일({font_path})을 찾을 수 없습니다. 기본 폰트로 PDF가 생성됩니다.")
            except Exception as e:
                st.error(f"폰트 등록 중 오류 발생: {e}. 기본 폰트로 PDF가 생성됩니다.")

            styles = getSampleStyleSheet()
            if font_registered:
                styles["Title"].fontName = "NanumGothic"
                styles["Normal"].fontName = "NanumGothic"
                styles["Heading1"].fontName = "NanumGothic"
                styles["Heading2"].fontName = "NanumGothic"
                # 필요시 다른 스타일도 설정

            elements = []  # PDF 내용을 담을 리스트 초기화

            # 1. 제목 추가
            elements.append(Paragraph("이사 견적서", styles["Title"]))
            elements.append(Spacer(1, 20)) # 제목 아래 간격 증가

            # 2. 기본 정보 표 추가
            elements.append(Paragraph("■ 기본 정보", styles["Heading2"]))
            elements.append(Spacer(1, 5)) # 섹션 제목 아래 작은 간격
            # 기본 정보 데이터 준비
            basic_data = [
                ["고객명", st.session_state.get("customer_name", "")],
                ["전화번호", st.session_state.get("customer_phone", "")],
                ["이사일", str(st.session_state.get("moving_date", ""))], # 날짜는 문자열로
                ["출발지", st.session_state.get("from_location", "")],
                ["도착지", st.session_state.get("to_location", "")],
                ["견적일", estimate_date], # Tab 1에서 계산된 값 사용
            ]
            # 기본 정보 테이블 생성 및 스타일 적용
            basic_table = Table(basic_data, colWidths=[100, 350]) # 너비 조정
            basic_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), "LEFT"),
                ('VALIGN', (0, 0), (-1, -1), "MIDDLE"), # 수직 정렬
                ('FONTNAME', (0, 0), (-1,-1), "NanumGothic" if font_registered else "Helvetica"), # 폰트 적용
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(basic_table)
            elements.append(Spacer(1, 12)) # 표 아래 간격

            # 3. 작업 정보 표 추가 (★ 새로 추가된 부분)
            elements.append(Paragraph("■ 작업 정보", styles["Heading2"]))
            elements.append(Spacer(1, 5))
            # 작업 정보 데이터 준비 (base_info 사용 전에 selected_vehicle 기반으로 다시 가져오기)
            current_base_info = {}
            if st.session_state.move_type == "가정 이사 🏠":
                current_base_info = home_vehicle_prices.get(selected_vehicle, {"men": 0, "housewife": 0})
            else:
                current_base_info = office_vehicle_prices.get(selected_vehicle, {"men": 0})
                current_base_info["housewife"] = 0 # 사무실 이사 시 주부 인원 0명 보장

            work_data = [
                ["선택 차량", selected_vehicle],
                ["출발지", f"{st.session_state.get('from_floor', '')}층 ({st.session_state.get('from_method', '')})"],
                ["도착지", f"{st.session_state.get('to_floor', '')}층 ({st.session_state.get('to_method', '')})"],
                ["기본 투입 인원", f"남성 {current_base_info.get('men', 0)}명" + (f", 여성 {current_base_info.get('housewife', 0)}명" if current_base_info.get('housewife', 0) > 0 else "")],
                ["추가 투입 인원", f"남성 {additional_men}명, 여성 {additional_women}명"],
            ]
            # 작업 정보 테이블 생성 및 스타일 적용
            work_table = Table(work_data, colWidths=[100, 350]) # 너비 조정
            work_table.setStyle(TableStyle([ # 동일한 스타일 적용 (기본 정보와)
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), "LEFT"),
                ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
                ('FONTNAME', (0, 0), (-1,-1), "NanumGothic" if font_registered else "Helvetica"),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(work_table)
            elements.append(Spacer(1, 12))

            # 4. 비용 상세 내역 표 추가 (★ 새로 추가된 부분)
            elements.append(Paragraph("■ 비용 상세 내역", styles["Heading2"]))
            elements.append(Spacer(1, 5))
            # 비용 데이터 준비 (Tab 3에서 계산된 cost_items 사용)
            cost_data = [["항목", "금액"]] # 헤더 추가
            cost_data.extend(cost_items) # 계산된 비용 항목 추가
            cost_data.append(["총 견적 비용", f"{total_cost:,}원"]) # 총 비용 추가
            # 비용 상세 내역 테이블 생성 및 스타일 적용
            cost_table = Table(cost_data, colWidths=[300, 150]) # 너비 조정
            cost_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),      # 첫 행(헤더) 배경색
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),      # 마지막 행(총계) 배경색
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), "LEFT"),
                ('ALIGN', (1, 1), (1, -1), "RIGHT"),                  # 금액 오른쪽 정렬 (헤더 제외)
                ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
                ('FONTNAME', (0, 0), (-1,-1), "NanumGothic" if font_registered else "Helvetica"),
                ('FONTNAME', (0, 0), (-1, 0), "NanumGothic" if font_registered else "Helvetica-Bold"), # 헤더 폰트 (Bold는 선택)
                ('FONTNAME', (0, -1), (-1,-1), "NanumGothic" if font_registered else "Helvetica-Bold"),# 총계 폰트 (Bold는 선택)
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(cost_table)
            elements.append(Spacer(1, 12))

            # 5. 특이 사항 추가
            special_notes_text = st.session_state.get("special_notes", "")
            if special_notes_text:
                elements.append(Paragraph("■ 특이 사항", styles["Heading2"]))
                elements.append(Spacer(1, 5))
                elements.append(Paragraph(special_notes_text, styles["Normal"]))
                elements.append(Spacer(1, 12))

            # PDF 빌드 (Try-Except 추가)
            try:
                doc.build(elements)

                # 다운로드 링크 생성
                pdf_data = buffer.getvalue()
                b64_pdf = base64.b64encode(pdf_data).decode("utf-8")
                file_name = f"이사견적서_{st.session_state.get('customer_name', '고객')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{file_name}">📥 견적서 다운로드</a>'
                st.markdown(href, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"PDF 문서 빌드 중 오류가 발생했습니다: {e}")
