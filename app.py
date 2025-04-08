import streamlit as st
from datetime import datetime
import pytz
import base64
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
pasted

코딩에서 # --- 품목 선택 및 박스 계산 ---
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
                qty = st.number_input(f"{item}", minvalue=0, step=1, key=f"{section}{item}")
                if qty > 0:
                    selected_items[item] = (qty, unit)
                    if item == "장롱":
                        additional_boxes["중대박스"] += qty * 5
                    if item == "붙박이장":
                        additional_boxes["옷박스"] += qty * 3
                    if item == "서랍장(5단)":
                        additional_boxes["중박스"] += qty * 5
# 박스 부피 계산
box_volumes = {"중대박스": 0.1875, "옷박스": 0.219, "중박스": 0.1}
total_volume = sum(items[sec][item][0] * qty for sec in items for item, (qty, ) in selecteditems.items() if item in items[sec])
total_volume += sum(box_volumes[box] * count for box, count in additional_boxes.items()) 
이부분은 생략 가능한 부분 아니야?

이 부분은 생략 가능한 부분이 아닙니다. 코드에서 이 섹션은 이사 견적 앱의 핵심 기능을 담당하고 있습니다:

"품목 선택 및 박스 계산" 부분은 사용자가 이사할 품목을 선택하고 수량을 입력하는 인터페이스를 생성합니다.
품목별로 부피와 무게 정보를 저장하고, 사용자가 선택한 품목에 따라 필요한 추가 박스(중대박스, 옷박스, 중박스)를 자동 계산합니다.
선택된 모든 품목의 총 부피를 계산하여 적절한 이사 차량을 추천하기 위한 기초 데이터를 제공합니다.
이 코드 부분을 생략하면:

사용자가 이사 품목을 선택할 수 없게 됩니다
총 부피와 무게 계산이 불가능해집니다
결과적으로 차량 추천이나 견적서 생성이 작동하지 않게 됩니다
추가로, 코드에 작은 오류가 있는 것 같습니다. 마지막 줄의 selected*items.items() 부분은 아마도 selected_items.items()로 써야 할 것 같습니다.

그럼 전체적으로 간소화 할 수 있는 부분이 확인해줘

이사 견적 앱 코드를 전체적으로 검토해 본 결과, 다음과 같은 부분에서 간소화가 가능합니다:

중복된 UI 코드 간소화:
비슷한 입력 필드들을 함수로 묶어 재사용할 수 있습니다.
예를 들어, create_input_field() 같은 함수를 만들어 반복되는 text_input 생성을 간소화할 수 있습니다.
품목 데이터 구조 개선:
현재 품목 데이터는 중첩 딕셔너리로 관리되고 있는데, 이를 외부 JSON 파일이나 CSV로 분리하여 코드 가독성을 높일 수 있습니다.
품목 추가/수정이 필요할 때 코드 변경 없이 데이터만 수정할 수 있게 됩니다.
PDF 생성 함수 모듈화:
PDF 생성 함수가 매우 길어 별도 모듈로 분리하면 유지보수가 편해집니다.
박스 계산 로직 개선:
현재는 if 문으로 특정 품목에 대한 추가 박스를 계산하는데, 이를 품목 데이터에 포함시켜 더 일관된 방식으로 처리할 수 있습니다.
예: '장롱': (1.05, 120.0, {'중대박스': 5}) 형식으로 데이터 구조 변경
차량 추천 로직 분리:
recommend_vehicle() 함수를 별도 유틸리티 모듈로 분리할 수 있습니다.
오류 처리 개선:
로고 이미지 불러오기 같은 비중요 기능의 예외 처리를 간소화하고, 필수 입력 검증을 강화할 수 있습니다.
스타일 일관성:
PDF와 UI의 스타일을 변수로 분리하여 일관성을 높이고 변경을 쉽게 할 수 있습니다.
이러한 간소화를 통해 코드의 유지보수성을 높이고, 기능 확장이 필요할 때 더 효율적으로 개발할 수 있습니다.

그렇게 수정해서 작성해줘


Optimized Moving Estimator App
코드 
코드를 다음과 같이 간소화했습니다:

주요 개선사항:
데이터 구조 개선:
품목 데이터를 통합된 구조로 재설계했습니다. 이제 각 품목은 부피와 무게뿐만 아니라 필요한 박스 정보와 단위까지 포함합니다.
이를 통해 품목별 특수 처리 로직(if문)이 사라지고 더 일관된 데이터 처리가 가능해졌습니다.
유틸리티 함수 추출:
create_labeled_input() 함수를 만들어 반복되는 입력 필드 생성을 간소화했습니다.
recommend_vehicle() 함수를 별도로 분리했습니다.
PDF 생성 함수 정리:
데이터를 구조화하여 함수에 전달, 가독성과 유지보수성을 향상시켰습니다.
메인 코드 구조화:
run_app() 함수를 만들어 앱의 메인 로직을 하나로 묶었습니다.
코드 가독성 개선:
코드를 논리적 섹션으로 나누어 가독성을 높였습니다.
일관된 스타일로 변수명을 정리했습니다.
이러한 변경으로 코드는 보다 유지보수가 쉽고, 기능 확장이 필요할 때 더 효율적으로 수정할 수 있게 되었습니다. 특히 품목 데이터를 별도 파일로 분리하면 더욱 관리가 용이해질 것입니다.

이 부분에 대해 더 자세히 설명해 주시겠어요?

            except Exception as e:
이 코드 부분은 예외 처리(Exception Handling)에 관한 것입니다. except Exception as e: 구문은 Python에서 예외가 발생했을 때 그 예외를 잡아서 처리하는 방법입니다.

상세 설명:
예외 처리의 목적:
프로그



import streamlit as st
import json
from datetime import datetime
import pytz
import base64
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO

# ============== 데이터 및 유틸리티 함수 ==============

# 품목 데이터 - 실제 구현시 외부 파일로 분리 가능
ITEMS_DATA = {
    '방': {
        '장롱': {'volume': 1.05, 'weight': 120.0, 'boxes': {'중대박스': 5}, 'unit': '칸'},
        '싱글침대': {'volume': 1.20, 'weight': 60.0, 'unit': '개'},
        '더블침대': {'volume': 1.70, 'weight': 70.0, 'unit': '개'},
        '돌침대': {'volume': 2.50, 'weight': 150.0, 'unit': '개'},
        '옷장': {'volume': 1.05, 'weight': 160.0, 'boxes': {'옷박스': 3}, 'unit': '개'},
        '서랍장(3단)': {'volume': 0.40, 'weight': 30.0, 'boxes': {'중박스': 3}, 'unit': '개'},
        '서랍장(5단)': {'volume': 0.75, 'weight': 40.0, 'boxes': {'중박스': 5}, 'unit': '개'},
        '화장대': {'volume': 0.32, 'weight': 80.0, 'unit': '개'},
        '중역책상': {'volume': 1.20, 'weight': 80.0, 'unit': '개'},
        '책장': {'volume': 0.96, 'weight': 56.0, 'unit': '개'},
        '책상&의자': {'volume': 0.25, 'weight': 40.0, 'unit': '개'},
        '옷행거': {'volume': 0.35, 'weight': 40.0, 'unit': '개'},
    },
    '거실': {
        '소파(1인용)': {'volume': 0.40, 'weight': 30.0, 'unit': '개'},
        '소파(3인용)': {'volume': 0.60, 'weight': 50.0, 'unit': '개'},
        '소파 테이블': {'volume': 0.65, 'weight': 35.0, 'unit': '개'},
        'TV(45인치)': {'volume': 0.15, 'weight': 15.0, 'unit': '개'},
        'TV(75인치)': {'volume': 0.30, 'weight': 30.0, 'unit': '개'},
        '장식장': {'volume': 0.75, 'weight': 40.0, 'unit': '개'},
        '오디오 및 스피커': {'volume': 0.10, 'weight': 20.0, 'unit': '개'},
        '에어컨': {'volume': 0.15, 'weight': 30.0, 'unit': '개'},
        '피아노(일반)': {'volume': 1.50, 'weight': 200.0, 'unit': '개'},
        '피아노(디지털)': {'volume': 0.50, 'weight': 50.0, 'unit': '개'},
        '안마기': {'volume': 0.90, 'weight': 50.0, 'unit': '개'},
        '공기청정기': {'volume': 0.10, 'weight': 8.0, 'unit': '개'}
    },
    '주방': {
        '양문형 냉장고': {'volume': 1.00, 'weight': 120.0, 'unit': '개'},
        '4도어 냉장고': {'volume': 1.20, 'weight': 130.0, 'unit': '개'},
        '김치냉장고(스탠드형)': {'volume': 0.80, 'weight': 90.0, 'unit': '개'},
        '김치냉장고(일반형)': {'volume': 0.60, 'weight': 60.0, 'unit': '개'},
        '식탁(4인)': {'volume': 0.40, 'weight': 50.0, 'unit': '개'},
        '식탁(6인)': {'volume': 0.60, 'weight': 70.0, 'unit': '개'},
        '가스레인지 및 인덕션': {'volume': 0.10, 'weight': 10.0, 'unit': '개'},
        '주방용 선반(수납장)': {'volume': 1.10, 'weight': 80.0, 'unit': '개'}
    },
    '기타': {
        '세탁기 및 건조기': {'volume': 0.50, 'weight': 80.0, 'unit': '개'},
        '신발장': {'volume': 1.10, 'weight': 60.0, 'unit': '개'},
        '여행가방 및 캐리어': {'volume': 0.15, 'weight': 5.0, 'unit': '개'},
        '화분': {'volume': 0.20, 'weight': 10.0, 'unit': '개'},
        '스타일러스': {'volume': 0.50, 'weight': 20.0, 'unit': '개'}
    }
}

BOX_VOLUMES = {"중대박스": 0.1875, "옷박스": 0.219, "중박스": 0.1}
METHOD_OPTIONS = ["사다리차", "승강기", "계단", "스카이"]

# 차량 추천 함수
def recommend_vehicle(total_volume, total_weight):
    vehicles = [
        ("1톤", 5, 1000), 
        ("2.5톤", 12, 2500), 
        ("5톤", 25, 5000), 
        ("6톤", 30, 6000),
        ("7.5톤", 40, 7500), 
        ("10톤", 50, 10000), 
        ("15톤", 70, 15000), 
        ("20톤", 90, 20000)
    ]
    loading_efficiency = 0.90

    for name, capacity, max_weight in vehicles:
        effective_capacity = capacity * loading_efficiency
        if total_volume <= effective_capacity and total_weight <= max_weight:
            remaining_space = (effective_capacity - total_volume) / effective_capacity * 100
            return name, remaining_space

    return "20톤 이상 차량 필요", 0

# UI 요소 생성 헬퍼 함수
def create_labeled_input(label, input_type, **kwargs):
    """재사용 가능한 라벨이 붙은 입력 필드 생성"""
    if input_type == "text":
        return st.text_input(label, **kwargs)
    elif input_type == "date":
        return st.date_input(label, **kwargs)
    elif input_type == "select":
        return st.selectbox(label, **kwargs)
    elif input_type == "textarea":
        return st.text_area(label, **kwargs)

# PDF 생성 함수
def create_pdf(customer_data, selected_items, additional_boxes, results, special_notes):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    content = []
    
    # 제목
    content.append(Paragraph("Moving Estimate", title_style))
    content.append(Spacer(1, 20))
    
    # 고객 정보 테이블
    customer_table_data = [
        ["Customer", customer_data['name'], "Phone", customer_data['phone']],
        ["From", f"{customer_data['from_location']} ({customer_data['from_floor']} {customer_data['from_method']})", 
         "To", f"{customer_data['to_location']} ({customer_data['to_floor']} {customer_data['to_method']})"],
        ["Estimate Date", customer_data['estimate_date'], "Moving Date", customer_data['moving_date'].strftime("%Y-%m-%d")]
    ]
    
    t = Table(customer_table_data, colWidths=[80, 120, 80, 120])
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
        ["Total Volume", f"{results['total_volume']:.2f} m³"],
        ["Recommended Vehicle", results['recommended_vehicle']],
        ["Remaining Space", f"{results['remaining_space']:.2f}%"]
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

# ============== 메인 앱 ==============

def run_app():
    # 로고 표시 (화면 좌측 상단)
    try:
        st.image("logo.png", width=150)
    except:
        st.write("로고 이미지를 찾을 수 없습니다.")

    # --- 고객 기본정보 입력 ---
    st.header("📝 고객 기본 정보")
    col1, col2 = st.columns(2)

    with col1:
        customer_name = create_labeled_input("👤 고객명", "text")
        from_location = create_labeled_input("📍 출발지", "text")

    with col2:
        customer_phone = create_labeled_input("📞 전화번호", "text")
        to_location = create_labeled_input("📍 도착지", "text")

    moving_date = create_labeled_input("🚚 이사일", "date")

    # 견적일 자동 표시 (현재시간)
    kst = pytz.timezone('Asia/Seoul')
    estimate_date = datetime.now(kst).strftime("%Y-%m-%d %H:%M")

    # --- 작업 조건 입력 ---
    st.header("🏢 작업 조건")
    col1, col2 = st.columns(2)

    with col1:
        from_floor = create_labeled_input("🔼 출발지 층수", "text")
        from_method = create_labeled_input("🛗 출발지 작업 방법", "select", options=METHOD_OPTIONS, key='from_method')

    with col2:
        to_floor = create_labeled_input("🔽 도착지 층수", "text")
        to_method = create_labeled_input("🛗 도착지 작업 방법", "select", options=METHOD_OPTIONS, key='to_method')

    special_notes = create_labeled_input("🗒️ 특이 사항 입력", "textarea", height=100, 
                                     placeholder="특이 사항이 있으면 입력해주세요.")

    # --- 품목 선택 및 계산 ---
    st.header("📋 품목 선택")
    selected_items = {}
    additional_boxes = {"중대박스": 0, "옷박스": 0, "중박스": 0}

    # 품목 선택 UI 생성
    for section, item_list in ITEMS_DATA.items():
        with st.expander(f"{section} 품목 선택"):
            cols = st.columns(3)
            items_list = list(item_list.items())
            third_len = len(items_list) // 3 + (len(items_list) % 3 > 0)
            
            for idx, (item, item_info) in enumerate(items_list):
                with cols[idx // third_len]:
                    unit = item_info.get('unit', '개')
                    qty = st.number_input(f"{item}", min_value=0, step=1, key=f"{section}_{item}")
                    
                    if qty > 0:
                        selected_items[item] = (qty, unit)
                        
                        # 추가 박스 계산
                        if 'boxes' in item_info:
                            for box_type, box_qty in item_info['boxes'].items():
                                additional_boxes[box_type] += qty * box_qty

    # 총 부피 및 무게 계산
    total_volume = 0
    total_weight = 0

    for section, item_list in ITEMS_DATA.items():
        for item, item_info in item_list.items():
            if item in selected_items:
                qty = selected_items[item][0]
                total_volume += item_info['volume'] * qty
                total_weight += item_info['weight'] * qty

    # 추가 박스 부피 계산
    total_volume += sum(BOX_VOLUMES[box] * count for box, count in additional_boxes.items())

    # 차량 추천
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

    # 선택한 품목 리스트 표시
    st.write("📋 **선택한 품목 리스트:**")
    if selected_items:
        cols = st.columns(3)
        items_list = list(selected_items.items())
        third_len = len(items_list) // 3 + (len(items_list) % 3 > 0)
        
        for idx, (item, (qty, unit)) in enumerate(items_list):
            with cols[idx // third_len]:
                st.write(f"- {item}: {qty}{unit}")
    else:
        st.info("선택한 품목이 없습니다.")

    # 특이 사항 출력
    if special_notes.strip():
        st.info(f"🗒️ **특이 사항:** {special_notes}")

    # 견적 결과 출력
    st.success(f"📐 총 부피: {total_volume:.2f} m³")
    st.success(f"🚛 추천 차량: {recommended_vehicle}")
    st.info(f"🧮 차량의 여유 공간: {remaining_space:.2f}%")

    # PDF 다운로드 버튼
    if st.button("PDF 견적서 다운로드"):
        if customer_name and from_location and to_location:
            try:
                # 결과 데이터 구성
                customer_data = {
                    'name': customer_name,
                    'phone': customer_phone,
                    'from_location': from_location,
                    'from_floor': from_floor,
                    'from_method': from_method,
                    'to_location': to_location,
                    'to_floor': to_floor,
                    'to_method': to_method,
                    'estimate_date': estimate_date,
                    'moving_date': moving_date
                }
                
                results = {
                    'total_volume': total_volume,
                    'total_weight': total_weight,
                    'recommended_vehicle': recommended_vehicle,
                    'remaining_space': remaining_space
                }
                
                pdf_buffer = create_pdf(customer_data, selected_items, additional_boxes, results, special_notes)
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

if __name__ == "__main__":
    run_app()
Claude
