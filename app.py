import streamlit as st
from datetime import datetime
import pytz
import base64
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO

# 로고 표시 (화면 좌측 상단)
try:
    st.image("logo.png", width=150)
except:
    st.write("로고 이미지를 찾을 수 없습니다.")

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
kst = pytz.timezone('Asia/Seoul')
estimate_date = datetime.now(kst).strftime("%Y-%m-%d %H:%M")


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

st.header("🗒️ 특이 사항 입력")
special_notes = st.text_area("특이 사항이 있으면 입력해주세요.", height=100)

# --- 품목 데이터 ---
items = {
    '방': {
        '장롱': (1.05, 120.0), '싱글침대': (1.20, 60.0), '더블침대': (1.70, 70.0), '돌침대': (2.50, 150.0),
        '옷장': (1.05, 160.0), '서랍장(3단)': (0.40, 30.0), '서랍장(5단)': (0.75, 40.0), '화장대': (0.32, 80.0),
        '중역책상': (1.20, 80.0), '책장': (0.96, 56.0), '책상&의자': (0.25, 40.0), '옷행거': (0.35, 40.0),
    },
    '거실': {
        '소파(1인용)': (0.40, 30.0), '소파(3인용)': (0.60, 50.0), '소파 테이블': (0.65, 35.0),
        'TV(45인치)': (0.15, 15.0), 'TV(75인치)': (0.30, 30.0), '장식장': (0.75, 40.0),
        '오디오 및 스피커': (0.10, 20.0), '에어컨': (0.15, 30.0), '피아노(일반)': (1.50, 200.0),
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


# --- 품목 선택 및 박스 계산 ---
st.header("📋 품목 선택")
selected_items = {}
additional_boxes = {"중대박스": 0, "옷박스": 0, "중박스": 0}

for section, item_list in items.items():
    with st.expander(f"{section} 품목 선택"):
        cols = st.columns(3)
        items_list = list(item_list.items())
        third_len = len(items_list) // 3 + (len(items_list) % 3 > 0)
        for idx, (item, (volume, weight)) in enumerate(items_list):
            with cols[idx // third_len]:
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

# --- 결과 출력 ---
st.subheader("✨ 실시간 견적 결과 ✨")
col1, col2 = st.columns(2)

with col1:
    st.write(f"👤 고객명: {customer_name}")
    st.write(f"📞 전화번호: {customer_phone}")
    st.write(f"📍 출발지: {from_location} ({from_floor} {from_method})")

with col2:
    st.write(f"📍 도착지: {to_location} ({to_floor} {to_method})")
    st.write(f"📅 견적일: {estimate_date}")
    st.write(f"🚚 이사일: {moving_date}")

st.write("📋 **선택한 품목 리스트:**")
cols = st.columns(3)  # 3열로 품목 리스트 표시 개선
items_list = list(selected_items.items())
third_len = len(items_list) // 3 + (len(items_list) % 3 > 0)
for idx, (item, (qty, unit)) in enumerate(items_list):
    with cols[idx // third_len]:
        st.write(f"- {item}: {qty}{unit}")

# 특이 사항 출력
if special_notes.strip():
    st.info(f"🗒️ **특이 사항:** {special_notes}")

st.success(f"📐 총 부피: {total_volume:.2f} m³")
st.success(f"🚛 추천 차량: {recommended_vehicle}")
st.info(f"🧮 차량의 여유 공간: {remaining_space:.2f}%")

# PDF 생성 함수 - 기본 폰트 사용
def create_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    # 기본 스타일 사용
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # 문서 내용 구성
    content = []
    
    # 제목
    content.append(Paragraph("Moving Estimate", title_style))
    content.append(Spacer(1, 20))
    
    # 고객 정보 테이블 (영문+숫자로 구성)
    customer_data = [
        ["Customer", customer_name, "Phone", customer_phone],
        ["From", f"{from_location} ({from_floor} {from_method})", "To", f"{to_location} ({to_floor} {to_method})"],
        ["Estimate Date", estimate_date, "Moving Date", moving_date.strftime("%Y-%m-%d")]
    ]
    
    t = Table(customer_data, colWidths=[80, 120, 80, 120])
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    content.append(t)
    content.append(Spacer(1, 20))
    
    # 품목 리스트 타이틀
    content.append(Paragraph("Selected Items", heading_style))
    content.append(Spacer(1, 10))
    
    # 품목 테이블 생성
    if selected_items:
        item_data = [["Item", "Quantity", "Unit"]]
        for item, (qty, unit) in selected_items.items():
            item_data.append([item, str(qty), unit])
        
        item_table = Table(item_data, colWidths=[220, 80, 80])
        item_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        content.append(item_table)
    else:
        content.append(Paragraph("No items selected.", normal_style))
    
    content.append(Spacer(1, 20))
    
    # 추가 박스 정보
    if any(additional_boxes.values()):
        content.append(Paragraph("Additional Boxes Required", heading_style))
        content.append(Spacer(1, 10))
        
        box_data = [["Box Type", "Quantity"]]
        for box, count in additional_boxes.items():
            if count > 0:
                box_data.append([box, str(count)])
        
        box_table = Table(box_data, colWidths=[220, 160])
        box_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        content.append(box_table)
        content.append(Spacer(1, 20))
    
    # 견적 결과
    content.append(Paragraph("Estimate Result", heading_style))
    content.append(Spacer(1, 10))
    
    result_data = [
        ["Total Volume", f"{total_volume:.2f} m³"],
        ["Recommended Vehicle", recommended_vehicle],
        ["Remaining Space", f"{remaining_space:.2f}%"]
    ]
    
    result_table = Table(result_data, colWidths=[180, 200])
    result_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    content.append(result_table)
    content.append(Spacer(1, 20))
    
    # 특이 사항
    if special_notes.strip():
        content.append(Paragraph("Special Notes", heading_style))
        content.append(Spacer(1, 10))
        content.append(Paragraph(special_notes, normal_style))
    
    # PDF 문서 생성
    doc.build(content)
    return buffer

# PDF 다운로드 버튼
if st.button("PDF 견적서 다운로드"):
    if customer_name and from_location and to_location:
        try:
            pdf_buffer = create_pdf()
            pdf_data = pdf_buffer.getvalue()
            b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
            
            # 다운로드 링크 생성
            pdf_filename = f"{customer_name}_moving_estimate.pdf"
            st.markdown(
                f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{pdf_filename}">📥 PDF 견적서 다운로드</a>',
                unsafe_allow_html=True
            )
            st.success("견적서가 생성되었습니다. 위 링크를 클릭하여 다운로드하세요.")
        except Exception as e:
            st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
    else:
        st.error("고객명, 출발지, 도착지를 모두 입력해주세요.")
