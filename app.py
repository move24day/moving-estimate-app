import streamlit as st
from datetime import datetime

# 로고 표시 (화면 좌측 상단)
st.image("logo.png", width=250)

# --- 고객 기본정보 입력 ---
st.header("📝 고객 기본 정보")
col1, col2 = st.columns(2)

with col1:
    customer_name = st.text_input("👤 고객명")
    from_location = st.text_input("📍 출발지")

with col2:
    customer_phone = st.text_input("📞 전화번호")
    to_location = st.text_input("📍 도착지")

moving_date = st.date_input("🚚 이사일")

# 견적일 자동 표시 (현재시간)
estimate_date = datetime.now().strftime("%Y-%m-%d %H:%M")

# --- 작업 조건 입력 ---
st.header("🏢 작업 조건")
col1, col2 = st.columns(2)

method_options = ["사다리차", "승강기", "계단", "스카이"]

with col1:
    from_floor = st.text_input("🔼 출발지 층수")
    from_method = st.selectbox("🛗 출발지 작업 방법", method_options, key='from_method')

with col2:
    to_floor = st.text_input("🔽 도착지 층수")
    to_method = st.selectbox("🛗 도착지 작업 방법", method_options, key='to_method')

# --- 품목 데이터 ---
items = {
    '방': {
        '장롱': (1.25, 120.0), '싱글침대': (1.20, 60.0), '더블침대': (1.70, 70.0), '돌침대': (2.50, 150.0),
        '옷장': (1.25, 160.0), '서랍장(3단)': (0.10, 30.0), '서랍장(5단)': (0.15, 40.0), '화장대': (0.32, 80.0),
        '중역책상': (1.20, 80.0), '책장': (0.96, 56.0), '책상&의자': (0.25, 40.0), '컴퓨터(노트북)': (0.03, 2.0)
    },
    '거실': {
        '소파(1인용)': (0.20, 30.0), '소파(3인용)': (0.60, 50.0), '소파(5인용)': (1.00, 80.0), '소파 테이블': (0.30, 15.0),
        'TV(45인치)': (0.07, 15.0), 'TV(65인치)': (0.10, 25.0), 'TV(75인치)': (0.12, 30.0), 'TV 장식장': (0.30, 40.0),
        '오디오 및 스피커': (0.10, 20.0), '에어컨': (0.15, 30.0), '선풍기': (0.15, 5.0), '피아노(일반)': (1.50, 200.0),
        '피아노(디지털)': (0.50, 50.0), '안마기': (0.60, 50.0), '공기청정기': (0.10, 8.0)
    },
    '주방': {
        '양문형 냉장고': (1.00, 120.0), '4도어 냉장고': (1.20, 130.0), '김치냉장고(스탠드형)': (0.80, 90.0), '김치냉장고': (0.60, 60.0),
        '식탁(2인)': (0.20, 30.0), '식탁(4인)': (0.40, 50.0), '식탁(6인)': (0.60, 70.0), '밥솥': (0.03, 5.0), '정수기': (0.03, 5.0),
        '가스레인지 및 인덕션': (0.10, 10.0), '음식물 처리기': (0.10, 20.0), '전자레인지': (0.05, 10.0), '믹서기': (0.02, 3.0),
        '주방용 선반(수납장)': (0.50, 30.0)
    },
    '기타': {
        '세탁기 및 건조기': (0.50, 80.0), '청소기': (0.10, 8.0), '다리미 및 다리미판': (0.05, 5.0), '빨래 건조대': (0.20, 3.0),
        '신발장': (0.60, 60.0), '여행가방 및 캐리어': (0.10, 5.0), '공구함 및 공구세트': (0.05, 10.0), '바구니': (0.01, 1.0),
        '중박스': (0.10, 2.0), '중대박스': (0.15, 3.0), '화분박스': (0.20, 3.0), '옷박스': (0.20, 4.0), '이불박스': (0.30, 5.0),
        '스타일러스': (0.10, 2.0)
    }
}


# --- 품목 선택 및 박스 계산 ---
st.header("📋 품목 선택")
selected_items = {}
additional_boxes = {"중대박스": 0, "옷박스": 0, "중박스": 0}

for section, item_list in items.items():
    with st.expander(f"{section} 품목 선택"):
        cols = st.columns(2)
        items_list = list(item_list.items())
        half_len = len(items_list) // 2 + len(items_list) % 2
        for idx, (item, (volume, weight)) in enumerate(items_list):
            with cols[idx // half_len]:
                unit = "칸" if item == "장롱" else "개"
                qty = st.number_input(f"{item}", min_value=0, step=1, key=f"{section}_{item}")
                if qty > 0:
                    selected_items[item] = (qty, unit)
                    if item == "장롱":
                        additional_boxes["중대박스"] += qty * 5
                    if item == "옷장":
                        additional_boxes["옷박스"] += qty * 3
                    if item == "서랍장(3단)":
                        additional_boxes["중박스"] += qty * 3
                    if item == "서랍장(5단)":
                        additional_boxes["중박스"] += qty * 5

# 박스 부피 계산
box_volumes = {"중대박스": 0.1875, "옷박스": 0.219, "중박스": 0.1}
total_volume = sum(items[sec][item][0] * qty for sec in items for item, (qty, _) in selected_items.items() if item in items[sec])
total_volume += sum(box_volumes[box] * count for box, count in additional_boxes.items())

# 차량 추천 및 여유공간 계산 (적재 효율 반영)
def recommend_vehicle(total_volume, total_weight):
    vehicles = [("1톤", 5, 1000), ("2.5톤", 12, 2500), ("5톤", 25, 5000), ("6톤", 30, 6000),
                ("7.5톤", 40, 7500), ("10톤", 50, 10000), ("15톤", 70, 15000), ("20톤", 90, 20000)]
    loading_efficiency = 0.90

    for name, capacity, max_weight in vehicles:
        effective_capacity = capacity * loading_efficiency
        if total_volume <= effective_capacity and total_weight <= max_weight:
            remaining_space = (effective_capacity - total_volume) / effective_capacity * 100
            return name, remaining_space

    return "20톤 이상 차량 필요", 0

# 총 무게 계산
total_weight = sum(items[sec][item][1] * qty for sec in items for item, (qty, _) in selected_items.items() if item in items[sec])

# 차량 추천 및 여유 공간 계산
recommended_vehicle, remaining_space = recommend_vehicle(total_volume, total_weight)

# 결과 출력
st.subheader("✨ 실시간 견적 결과 ✨")
col1, col2 = st.columns(2)

with col1:
    st.write(f"👤 고객명: {customer_name}")
    st.write(f"📞 전화번호: {customer_phone}")
    st.write(f"📍 출발지: {from_location} ({from_floor}, {from_method})")

with col2:
    st.write(f"📍 도착지: {to_location} ({to_floor}, {to_method})")
    st.write(f"📅 견적일: {estimate_date}")
    st.write(f"🚚 이사일: {moving_date}")

st.write("📋 **선택한 품목 리스트:**")
cols = st.columns(2)
items_list = list(selected_items.items())
half_len = len(items_list) // 2 + len(items_list) % 2
for idx, (item, (qty, unit)) in enumerate(items_list):
    with cols[idx // half_len]:
        st.write(f"- {item}: {qty}{unit}")


st.success(f"📐 총 부피: {total_volume:.2f} m³")
st.success(f"🚛 추천 차량: {recommended_vehicle}")
st.info(f"🧮 차량의 여유 공간: {remaining_space:.2f}%")
