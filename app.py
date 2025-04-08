import streamlit as st
from datetime import datetime
import pytz
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

# 한글 폰트 설정
pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic.ttf'))

# 로고
st.image("logo.png", width=150)

st.header("📝 고객 기본 정보")
col1, col2 = st.columns(2)

with col1:
    customer_phone = st.text_input("📞 전화번호")
    from_location = st.text_input("📍 출발지")

with col2:
    to_location = st.text_input("📍 도착지")

moving_date = st.date_input("🚚 이사일")

kst = pytz.timezone('Asia/Seoul')
estimate_date = datetime.now(kst).strftime("%Y-%m-%d %H:%M")

st.header("🏢 이사 유형")
moving_type = st.radio("이사 유형을 선택해주세요", ["가정 이사", "사무실 이사"])

st.header("📅 특정일 체크")
special_days = st.multiselect("특정일 체크 (각 항목당 10만원 추가)", ["금요일", "말일", "손없는 날", "이사 많은 날"])

st.header("🏢 작업 조건")
col1, col2 = st.columns(2)

methods = ["사다리차", "승강기", "계단", "스카이"]

with col1:
    from_floor = st.number_input("🔼 출발지 층수", min_value=0, step=1)
    from_method = st.selectbox("🛗 출발지 작업 방법", methods)

with col2:
    to_floor = st.number_input("🔽 도착지 층수", min_value=0, step=1)
    to_method = st.selectbox("🛗 도착지 작업 방법", methods)

st.header("🗒️ 특이 사항 입력")
special_notes = st.text_area("특이 사항 입력", height=80)

base_price_table = {
    "1톤": 40, "2.5톤": 90, "5톤": 120, "6톤": 135, "7.5톤": 175, "10톤": 230
}

# 차량추천 간소화 (예시용)
recommended_vehicle = "5톤"
base_price = base_price_table[recommended_vehicle]

special_day_prices = {"금요일": 10, "말일": 10, "손없는 날": 10, "이사 많은 날": 10}
special_day_cost = sum(special_day_prices[day] for day in special_days)

ladder_cost = 0  # 예시 단순화

total_cost = base_price + special_day_cost + ladder_cost

st.subheader("✨ 실시간 견적 결과 ✨")
st.success(f"총 비용: {total_cost}만원")

if special_days:
    st.info(f"📅 특정일 추가 비용: +{special_day_cost}만원 ({', '.join(special_days)})")

# PDF 생성 함수
def create_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('Korean', fontName='NanumGothic', fontSize=12))

    content = []
    content.append(Paragraph("이사 견적서", styles['Title']))
    content.append(Spacer(1, 10))

    data = [
        ["전화번호", customer_phone, "이사일", moving_date.strftime("%Y-%m-%d")],
        ["출발지", f"{from_location}({from_floor}층, {from_method})", "도착지", f"{to_location}({to_floor}층, {to_method})"],
        ["견적일", estimate_date, "이사 유형", moving_type],
        ["기본 이사 비용", f"{base_price}만원", "특정일 추가 비용", f"{special_day_cost}만원"],
        ["총 이사 비용", f"{total_cost}만원", "특이사항", special_notes if special_notes else "없음"]
    ]

    table = Table(data, colWidths=[70*mm, 40*mm, 70*mm, 40*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'NanumGothic'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    content.append(table)
    doc.build(content)

    return buffer.getvalue()

# PDF 다운로드 버튼
pdf_data = create_pdf()
pdf_filename = f"{customer_phone if customer_phone else '고객'}_이사_견적서.pdf"
st.download_button("📥 견적서 PDF 다운로드", pdf_data, pdf_filename, mime="application/pdf")
