import streamlit as st
from datetime import datetime
import pytz

# 로고
st.image("logo.png", width=250)

# 제목
st.title("🚚 이사 견적 산정 시스템")

# --- 고객 기본 정보 ---
st.header("📝 고객 기본 정보")
col1, col2 = st.columns(2)
with col1:
    customer_name = st.text_input("👤 고객명")
    from_location = st.text_input("📍 출발지")
with col2:
    customer_phone = st.text_input("📞 전화번호")
    to_location = st.text_input("📍 도착지")
moving_date = st.date_input("📅 이사일")

kst = pytz.timezone('Asia/Seoul')
estimate_date = datetime.now(kst).strftime("%Y-%m-%d %H:%M")

if not customer_name or not customer_phone:
    st.warning("고객명과 전화번호를 입력해주세요.")
    st.stop()

# --- 작업 조건 ---
st.header("🏢 작업 조건")
col1, col2 = st.columns(2)
methods = ["사다리차", "승강기", "계단", "스카이"]
with col1:
    from_floor = st.text_input("🔼 출발지 층수")
    from_method = st.selectbox("🛗 출발지 작업 방법", methods)
with col2:
    to_floor = st.text_input("🔽 도착지 층수")
    to_method = st.selectbox("🛗 도착지 작업 방법", methods, key="to_method")

# --- 품목 데이터 ---
items = {
    '방': {
        '장롱': (1.05, 120.0), '싱글침대': (1.20, 60.0), '더블침대': (1.70, 70.0), '돌침대': (2.50, 150.0),
        '옷장': (1.05, 160.0), '서랍장(3단)': (0.40, 30.0), '서랍장(5단)': (0.75, 40.0), '화장대': (0.32, 80.0),
        '중역책상': (1.20, 80.0), '책장': (0.96, 56.0), '책상&의자': (0.25, 40.0),
    },
    '거실': {
        '소파(1인용)': (0.40, 30.0), '소파(3인용)': (0.60, 50.0), '소파 테이블': (0.30, 15.0),
        'TV(45인치)': (0.07, 15.0), 'TV(75인치)': (0.12, 30.0), '장식장': (0.60, 40.0),
        '오디오 및 스피커': (0.10, 20.0), '에어컨': (0.15, 30.0), '선풍기': (0.05, 5.0), '피아노(일반)': (1.50, 200.0),
        '피아노(디지털)': (0.50, 50.0), '안마기': (0.90, 50.0), '공기청정기': (0.10, 8.0)
    },
    '주방': {
        '양문형 냉장고': (1.00, 120.0), '4도어 냉장고': (1.20, 130.0), '김치냉장고(스탠드형)': (0.80, 90.0), '김치냉장고(일반형)': (0.60, 60.0),
        '식탁(4인)': (0.40, 50.0), '식탁(6인)': (0.60, 70.0),
        '가스레인지 및 인덕션': (0.10, 10.0),
        '주방용 선반(수납장)': (1.10, 80.0)
    },
    '기타': {
        '세탁기 및 건조기': (0.50, 80.0),
        '신발장': (1.10, 60.0), '여행가방 및 캐리어': (0.15, 5.0), '화분': (0.20, 10.0), 
        '스타일러스': (0.50, 20.0)
    }
}


# --- 품목 선택 ---
st.header("📦 품목 선택")
items = {...}  # 기존 제공된 품목 데이터를 입력하세요

selected_items = {}
tabs = st.tabs(items.keys())

for tab, (section, item_dict) in zip(tabs, items.items()):
    with tab:
        for item, (volume, weight) in item_dict.items():
            unit = "칸" if item == "장롱" else "개"
            qty = st.number_input(f"{item}", min_value=0, step=1, key=f"{section}_{item}")
            if qty > 0:
                selected_items[item] = (qty, volume, weight)

# --- 부피 및 무게 산정 ---
total_volume = sum(qty * volume for qty, volume, _ in selected_items.values())
total_weight = sum(qty * weight for qty, _, weight in selected_items.values())

# 추가 박스 계산
additional_boxes = {"중대박스": 0, "옷박스": 0, "중박스": 0}
for item, (qty, _, _) in selected_items.items():
    if item == "장롱":
        additional_boxes["중대박스"] += qty * 5
    if item == "옷장":
        additional_boxes["옷박스"] += qty * 3
    if item == "서랍장(3단)":
        additional_boxes["중박스"] += qty * 3
    if item == "서랍장(5단)":
        additional_boxes["중박스"] += qty * 5

box_volumes = {"중대박스": 0.1875, "옷박스": 0.219, "중박스": 0.1}
for box, count in additional_boxes.items():
    total_volume += box_volumes[box] * count

# --- 차량 추천 ---
def recommend_vehicle(volume, weight):
    vehicles = [("1톤", 5, 1000), ("2.5톤", 12, 2500), ("5톤", 25, 5000), ("6톤", 30, 6000),
                ("7.5톤", 40, 7500), ("10톤", 50, 10000), ("15톤", 70, 15000), ("20톤", 90, 20000)]
    efficiency = 0.90
    for name, cap, max_w in vehicles:
        effective_cap = cap * efficiency
        if volume <= effective_cap and weight <= max_w:
            space_left = (effective_cap - volume) / effective_cap * 100
            return name, space_left
    return "20톤 이상 차량 필요", 0

vehicle, space_left = recommend_vehicle(total_volume, total_weight)

# --- 결과 출력 ---
st.subheader("📋 견적 결과")
st.markdown(f"""
| 항목      | 내용 |
|-----------|------|
| 고객명    | {customer_name} |
| 전화번호  | {customer_phone} |
| 출발지    | {from_location} ({from_floor}층, {from_method}) |
| 도착지    | {to_location} ({to_floor}층, {to_method}) |
| 견적일    | {estimate_date} |
| 이사일    | {moving_date} |
| 총 부피   | {total_volume:.2f} m³ |
| 총 무게   | {total_weight:.1f} kg |
| 추천 차량 | {vehicle} |
| 여유 공간 | {space_left:.1f}% |
""")

st.subheader("📑 선택된 품목")
for item, (qty, _, _) in selected_items.items():
    st.write(f"- {item}: {qty}개")

# --- PDF 다운로드 기능 예시 ---
# st.download_button("📥 견적서 PDF 다운로드", pdf_bytes, file_name="견적서.pdf")
