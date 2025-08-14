import streamlit as st
import random
import string
from datetime import datetime, timedelta

st.markdown(
    """<style>
    .stApp {
        background-color: #fffbea;
        color: #000;
    }
    .stButton>button {
        background-color: #f5b800;
        color: black;
        border: none;
    }
    </style>""",
    unsafe_allow_html=True
)

if 'cards_db' not in st.session_state:
    st.session_state.cards_db = {}
if 'transactions_db' not in st.session_state:
    st.session_state.transactions_db = []
if 'custom_allowed_sites_input' not in st.session_state:
    st.session_state.custom_allowed_sites_input = "amazon.com\nkbstar.com\ntemu.com"
if 'pending_payment' not in st.session_state:
    st.session_state.pending_payment = None

def ai_recommend():
    return {
        "limit": random.choice([50, 100, 150, 200, 500]),
        "duration_days": random.choice([1, 3, 7, 14, 30]),
        "restricted_sites": random.choice([True, False])
    }

def generate_card_id():
    num_part = ''.join(random.choices(string.digits, k=3))
    alpha_part = ''.join(random.choices(string.ascii_uppercase, k=3))
    return f"CARD{num_part}-{alpha_part}"

def calculate_risk(payment_amount, card, site, country):
    risk = 0
    reasons = []
    if payment_amount > 0.8 * card['limit']:
        risk += 0.3
        reasons.append('결제금액이 카드 한도 근접')
    if country in ['NG', 'RU']:
        risk += 0.5
        reasons.append(f'고위험 국가: {country}')
    if card['restricted'] and card.get('allowed_sites') and site not in card['allowed_sites']:
        risk += 0.4
        reasons.append('허용되지 않은 사이트')
    risk += random.random() * 0.2
    risk = min(risk, 1.0)
    return risk, reasons

st.title("가상카드 발급 & 결제 시뮬레이션")

st.header("1. 카드 발급")
purpose = st.text_input("거래 목적", "해외 쇼핑")
amount = st.number_input("결제 한도", min_value=1, max_value=5000, value=100, step=10)
duration = st.number_input("유효 기간(일)", min_value=1, max_value=365, value=7)
restrict_sites = st.checkbox("사용처 제한", value=True)

allowed_sites_list = None
if restrict_sites:
    st.info("결제를 허용할 사이트를 입력하세요. 한 줄에 하나씩 입력합니다.")
    st.session_state.custom_allowed_sites_input = st.text_area(
        "허용 사이트 목록",
        st.session_state.custom_allowed_sites_input,
        height=100,
    )
    allowed_sites_list = [s.strip() for s in st.session_state.custom_allowed_sites_input.split('\n') if s.strip()]

ai_cond = ai_recommend()
st.caption(f"AI 추천 조건 예시 → limit: {ai_cond['limit']}, duration_days: {ai_cond['duration_days']}, restricted_sites: {ai_cond['restricted_sites']}")

if st.button("카드 발급"):
    card_id = generate_card_id()
    expiry = datetime.now() + timedelta(days=int(duration))
    st.session_state.cards_db[card_id] = {
        "purpose": purpose,
        "limit": int(amount),
        "expiry": expiry,
        "restricted": bool(restrict_sites),
        "allowed_sites": allowed_sites_list if restrict_sites else None,
        "active": True,
    }
    st.success(f"{card_id} 발급 완료! 유효기간: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")

st.header("2. 결제 요청")
if st.session_state.cards_db:
    selected_card = st.selectbox("결제에 사용할 카드 선택", options=list(st.session_state.cards_db.keys()))
    payment_amount = st.number_input("결제 금액", min_value=1, max_value=5000, value=80, step=10, key="pay_amount")
    site = st.text_input("결제 사이트", "amazon.com", key="pay_site")
    country = st.text_input("사용 국가", "KR", key="pay_country")

    if st.button("결제 시도"):
        card = st.session_state.cards_db[selected_card]
        if payment_amount > card['limit']:
            st.error("결제 금액이 카드 한도를 초과했습니다.")
        elif card['expiry'] < datetime.now():
            st.error("카드 유효기간이 만료되었습니다.")
        else:
            risk_score, reasons = calculate_risk(payment_amount, card, site, country)
            # AI 위험 분석 팝업
            st.info(f"AI 위험 점수: {risk_score:.2f} | 분석 사유: {', '.join(reasons)}")
            if risk_score > 0.5:
                st.warning("AI 위험 탐지, 결제를 보류합니다.")
                st.session_state.pending_payment = {
                    'card_id': selected_card,
                    'amount': int(payment_amount),
                    'site': site,
                    'country': country,
                    'risk_score': risk_score,
                    'reasons': reasons
                }
            else:
                st.success(f"결제 승인 완료 (AI 위험 점수: {risk_score:.2f})")
                card['active'] = False
                st.info("유효 기간이 지나면 자동 폐기됩니다.")
                st.session_state.transactions_db.append({
                    'card': selected_card,
                    'amount': int(payment_amount),
                    'site': site,
                    'country': country,
                    'risk_score': risk_score,
                    'reasons': reasons
                })

    if st.session_state.pending_payment:
        pp = st.session_state.pending_payment
        card = st.session_state.cards_db[pp['card_id']]
        st.subheader("추가 확인 필요")
        st.info(
            f"AI 위험 탐지로 결제가 보류되었습니다.\n카드: {pp['card_id']} | 금액: {pp['amount']} | 사이트: {pp['site']} | 국가: {pp['country']}\n위험 점수: {pp['risk_score']:.2f}\n사유: {', '.join(pp['reasons'])}"
        )
        choice = st.radio("무시하고 다시 결제를 진행하시겠습니까?", ("아니오", "예"), key="override_choice")
        if choice == "예":
            if st.button("본인인증 진행", key="do_auth"):
                st.success("결제 승인 완료")
                card['active'] = False
                st.info("유효 기간이 지나면 자동 폐기됩니다.")
                st.session_state.transactions_db.append({
                    'card': pp['card_id'],
                    'amount': pp['amount'],
                    'site': pp['site'],
                    'country': pp['country'],
                    'risk_score': pp['risk_score'],
                    'reasons': pp['reasons']
                })
                st.session_state.pending_payment = None
        else:
            st.info("결제가 취소되었습니다.")
            if st.button("보류된 결제 닫기", key="close_pending"):
                st.session_state.pending_payment = None
else:
    st.info("먼저 카드를 발급해주세요.")

st.header("3. 거래 기록 확인")
if st.session_state.transactions_db:
    st.table(st.session_state.transactions_db)
else:
    st.write("거래 기록이 없습니다.")
