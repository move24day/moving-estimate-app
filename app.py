import streamlit as st

# 로고 이미지 추가
title_col1, title_col2 = st.columns([1, 3])
with title_col1:
    st.image("logo.png", width=100)
with title_col2:
    st.title("이삿날 견적물량 체크")

# 품목별 데이터(부피 단위: ㎥)
items = {
    "🗄️ 장롱": 5.0,
    "🧊 냉장고": 3.5,
    "🛏️ 침대": 4.0,
    "🛋️ 소파": 3.0,
    "🗃️ 서랍장": 1.5,
    "🧺 세탁기": 1.0,
    "❄️ 에어컨": 1.0,
    "📺 TV": 0.5,
    "🎹 피아노": 2.5
}

# 차량 데이터
vehicles = [
    {"type": "🚚 1톤 트럭", "capacity": 5},
    {"type": "🚛 2.5톤 트럭", "capacity": 15},
    {"type": "🚛 5톤 트럭", "capacity": 35},
    {"type": "🚛 10톤 트럭", "capacity": 50}
]

# 견적 계산 함수
def calculate_estimate(selected_items):
    total_volume = sum(items[item] * quantity for item, quantity in selected_items.items())
    selected_vehicle = next((vehicle for vehicle in vehicles if total_volume <= vehicle["capacity"]), vehicles[-1])
    capacity_usage = (total_volume / selected_vehicle["capacity"]) * 100
    remaining_capacity = 100 - capacity_usage
    return total_volume, selected_vehicle, remaining_capacity

# Streamlit UI
st.header("📋 이삿짐 품목 선택")
selected_items = {}
cols = st.columns(2)
for idx, item in enumerate(items):
    quantity = cols[idx % 2].number_input(f"{item}", min_value=0, step=1, key=item)
    if quantity > 0:
        selected_items[item] = quantity

# 실시간 계산 (버튼 누를 필요 없음)
if selected_items:
    total_volume, vehicle, remaining_capacity = calculate_estimate(selected_items)

    st.subheader("📌 차량 선택 결과")
    st.info(f"📐 **총 부피:** {total_volume:.1f}㎥")
    st.success(f"🚛 **추천 차량:** {vehicle['type']}")
    st.warning(f"📉 **차량 여유 공간:** {remaining_capacity:.1f}%")