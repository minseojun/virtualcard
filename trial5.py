import streamlit as st
import random
from datetime import datetime, timedelta

# 데이터 저장
if 'cards_db' not in st.session_state:
    st.session_state.cards_db = {}
if 'transactions_db' not in st.session_state:
    st.session_state.transactions_db = []
if 'pending_payment' not in st.session_state:
    st.session_state.pending_payment = None
if 'custom_allowed_sites' not in st.session_state:
    st.session_state.custom_allowed_sites = []

# AI 추천 조건
def ai_recommend():
    return {
        "limit": random.choice([50, 100, 150, 200, 500]),
        "duration_days": random.choice([1, 3, 7, 14, 30]),
        "restricted_sites": random.choice([True, False])
    }

st.title("가상카드 발급 & 결제 시뮬레이션")

# 카드 발급 UI
st.header("1. 카드 발급")
purpose = st.text_input("거래 목적", "해외 쇼핑")
amount = st.number_input("결제 한도", min_value=1, max_value=5000, value=100, step=10)
duration = st.number_input("유효 기간(일)", min_value=1, max_value=365, value=7)
restrict_sites = st.checkbox("사용처 제한", value=True)

if restrict_sites:
    sites_input = st.text_area("결제를 허용할 사이트를 입력하세요 (줄바꿈으로 구분)", "amazon.com\nkbstar.com\ntemu.com")
    st.session_state.custom_allowed_sites = [s.strip() for s in sites_input.split('\n') if s.strip()]

ai_cond = ai_recommend()
st.write(f"AI 추천 조건: {ai_cond}")

if st.button("카드 발급"):
    card_id = f"CARD{len(st.session_state.cards_db)+1:03d}"
    expiry = datetime.now() + timedelta(days=duration)
    st.session_state.cards_db[card_id] = {
        "purpose": purpose,
        "limit": amount,
        "expiry": expiry,
        "restricted": restrict_sites,
        "active": True
    }
    st.success(f"{card_id} 발급 완료! 유효기간: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")

# 결제 요청 UI
st.header("2. 결제 요청")
if st.session_state.cards_db:
    selected_card = st.selectbox("결제에 사용할 카드 선택", options=list(st.session_state.cards_db.keys()))
    payment_amount = st.number_input("결제 금액", min_value=1, max_value=5000, value=80, step=10)
    site = st.text_input("결제 사이트", "amazon.com")
    country = st.text_input("사용 국가", "KR")

    if st.button("결제 시도"):
        card = st.session_state.cards_db[selected_card]
        allowed_sites = st.session_state.custom_allowed_sites if card['restricted'] else []

        if payment_amount > card['limit']:
            st.error("결제 금액이 카드 한도를 초과했습니다.")
        elif card['expiry'] < datetime.now():
            st.error("카드 유효기간이 만료되었습니다.")
        elif card['restricted'] and site not in allowed_sites:
            st.warning("AI 위험 탐지, 결제를 보류합니다")
            if st.radio("무시하고 다시 결제를 진행하시겠습니까?", ("아니오", "예")) == "예":
                if st.button("본인인증 진행"):
                    st.success("결제 승인 완료")
                    card['active'] = False
                    st.info("카드 자동 폐기 처리됨")
                    st.session_state.transactions_db.append({
                        'card': selected_card,
                        'amount': payment_amount,
                        'site': site,
                        'country': country,
                        'risk_score': "Bypassed"
                    })
            else:
                st.info("결제가 취소되었습니다.")
        else:
            risk_score = random.random()
            if risk_score > 0.8 or country in ['NG', 'RU']:
                st.warning("AI 위험 탐지, 결제를 보류합니다")
            else:
                st.success("결제 승인 완료")
                card['active'] = False
                st.info("카드 자동 폐기 처리됨")
            st.session_state.transactions_db.append({
                'card': selected_card,
                'amount': payment_amount,
                'site': site,
                'country': country,
                'risk_score': risk_score
            })
else:
    st.info("먼저 카드를 발급해주세요.")

# 거래 기록 확인
st.header("3. 거래 기록 확인")
if st.session_state.transactions_db:
    st.table(st.session_state.transactions_db)
else:
    st.write("거래 기록이 없습니다.")
