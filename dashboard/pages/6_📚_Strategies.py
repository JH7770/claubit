"""
Strategy Encyclopedia Page

Comprehensive documentation of all available trading strategies,
including their logic, parameters, and use cases.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime

from dashboard.utils.theme import apply_dark_mode_css, initialize_dark_mode


st.set_page_config(page_title="전략 백과사전", page_icon="📚", layout="wide")

# Initialize dark mode immediately to prevent flash
initialize_dark_mode()

# Apply dark mode CSS
apply_dark_mode_css()

# Title
st.title("📚 전략 백과사전")
st.markdown("**US Market Volatility Hunter의 모든 트레이딩 전략 상세 가이드**")
st.markdown("---")

# Strategy Categories
st.markdown("### 📂 전략 분류")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **추세 추종 전략**
    - Volatility Breakout
    - MACD Momentum
    - Supertrend
    - Volume MA Cross
    """)

with col2:
    st.success("""
    **평균 회귀 전략**
    - RSI + Bollinger Reversion
    - Keltner Channel Reversion
    """)

with col3:
    st.warning("""
    **하이브리드 전략**
    - Dynamic Scalping Grid
    - Stochastic Momentum
    """)

st.markdown("---")

# Strategy filter
strategy_type = st.selectbox(
    "전략 필터링",
    ["모든 전략", "추세 추종", "평균 회귀", "하이브리드"]
)

st.markdown("---")

# Strategy Documentation

strategies = [
    {
        "code": "ST-01",
        "name": "Volatility Breakout",
        "name_kr": "변동성 돌파",
        "type": "추세 추종",
        "description": "Larry Williams의 변동성 돌파 컨셉에서 영감을 받은 전략. 미국 시장 시간대 동안 변동성 확장을 감지하고 가격이 이전 변동 범위를 돌파할 때 진입합니다.",
        "best_for": "높은 변동성이 예상되는 US 시장 개장 시간대",
        "entry_logic": [
            "**롱 진입**: 현재가 > 시가 + (범위 × k)",
            "**숏 진입**: 현재가 < 시가 - (범위 × k)",
            "범위 = 이전 세션의 고가 - 저가",
            "선택사항: 이동평균 필터로 추세 확인"
        ],
        "exit_logic": [
            "익절: 진입가 대비 4.0% 수익 (기본값)",
            "손절: 진입가 대비 2.0% 손실 (기본값)",
            "시간 기반 청산: 최대 8시간 보유"
        ],
        "parameters": {
            "k": "돌파 임계값 노이즈 비율 (0.3-0.8). 낮을수록 조기 진입하지만 휩쏘 위험 증가",
            "lookback_period": "범위 계산을 위한 시간 단위 (4, 8, 12, 24)",
            "ma_period": "추세 필터용 이동평균 기간 (5, 10, 20, 50)",
            "use_ma_filter": "MA 추세 필터링 활성화 여부",
            "stop_loss_percent": "손절매 비율 (기본값: 2.0%)",
            "take_profit_percent": "익절 비율 (기본값: 4.0%)"
        },
        "strengths": [
            "변동성 급증 시 탁월한 성능",
            "명확한 진입/청산 규칙",
            "US 시장 개장 시간대에 최적화"
        ],
        "weaknesses": [
            "횡보장에서 잦은 휩쏘 발생",
            "낮은 변동성 구간에서 성능 저하"
        ]
    },
    {
        "code": "ST-02",
        "name": "RSI + Bollinger Reversion",
        "name_kr": "RSI + 볼린저 평균회귀",
        "type": "평균 회귀",
        "description": "RSI와 볼린저 밴드를 결합하여 과매수/과매도 상태를 식별하는 평균회귀 전략. 횡보장에서 최적의 성능을 발휘합니다.",
        "best_for": "횡보하는 레인지 시장, 낮은 추세 강도",
        "entry_logic": [
            "**롱 진입**: 가격 < BB 하단 AND RSI < 매수 임계값 (과매도)",
            "**숏 진입**: 가격 > BB 상단 AND RSI > 매도 임계값 (과매수)",
            "두 지표 모두 극단 상태를 확인해야 진입"
        ],
        "exit_logic": [
            "목표: 가격이 BB 중간선으로 회귀 (평균회귀 완료)",
            "손절: 밴드 폭을 넘어 가격이 계속 이탈 (추세 형성)",
            "시간 기반 청산: 최대 4시간 보유 (평균회귀는 빠르게 발생해야 함)"
        ],
        "parameters": {
            "rsi_period": "RSI 계산 기간 (9-21, 기본값: 14)",
            "rsi_buy_threshold": "롱 진입 RSI 수준 (20-35)",
            "rsi_sell_threshold": "숏 진입 RSI 수준 (65-80)",
            "bb_period": "볼린저 밴드 SMA 기간 (기본값: 20)",
            "bb_stddev": "BB 표준편차 승수 (1.8-2.5)",
            "stop_loss_percent": "손절매 비율 (기본값: 2.0%)",
            "take_profit_percent": "익절 비율 (기본값: 4.0%)"
        },
        "strengths": [
            "횡보장에서 높은 승률",
            "두 지표의 확인으로 신뢰도 향상",
            "명확한 진입 조건"
        ],
        "weaknesses": [
            "추세장에서 반복적인 손실 (falling knife)",
            "평균회귀가 발생하지 않으면 손실",
            "강한 추세에서는 부적합"
        ]
    },
    {
        "code": "ST-03",
        "name": "Volume Weighted MA Cross",
        "name_kr": "거래량 가중 이동평균 교차",
        "type": "추세 추종",
        "description": "전통적인 이동평균 교차 전략에 거래량 확인을 추가. 거래량 급증 시에만 교차 신호를 받아 허위 신호를 줄입니다.",
        "best_for": "추세 시장, 거래량이 많은 변동성 구간",
        "entry_logic": [
            "**골든 크로스 (롱)**: 빠른 MA가 느린 MA를 상향 돌파",
            "  AND 거래량 > 평균 거래량 × 승수",
            "**데드 크로스 (숏)**: 빠른 MA가 느린 MA를 하향 돌파",
            "  AND 거래량 > 평균 거래량 × 승수",
            "거래량 확인이 핵심 차별화 요소"
        ],
        "exit_logic": [
            "반대 방향 교차 신호",
            "손절/익절 달성",
            "시간 기반 청산: 최대 12시간 (추세 발전 시간 필요)"
        ],
        "parameters": {
            "short_window": "빠른 MA 기간 (5-20, 기본값: 10)",
            "long_window": "느린 MA 기간 (20-60, 기본값: 30)",
            "vol_lookback": "평균 거래량 기간 (기본값: 20)",
            "vol_multiplier": "거래량 임계값 승수 (1.2-3.0)",
            "stop_loss_percent": "손절매 비율 (기본값: 2.0%)",
            "take_profit_percent": "익절 비율 (기본값: 4.0%)"
        },
        "strengths": [
            "거래량 필터로 신뢰도 높은 신호",
            "강한 모멘텀 움직임 포착",
            "허위 돌파 감소"
        ],
        "weaknesses": [
            "횡보장에서 지연된 진입",
            "거래량 급증 이후 진입 시 늦을 수 있음",
            "빠른 반전에 취약"
        ]
    },
    {
        "code": "ST-04",
        "name": "Dynamic Scalping Grid",
        "name_kr": "동적 스캘핑 그리드",
        "type": "하이브리드",
        "description": "현재 가격 위아래에 그리드 주문을 배치. ATR 기반으로 간격이 변동성에 맞춰 조정됩니다. 레인지 시장에서 가격 진동으로 수익을 냅니다.",
        "best_for": "횡보하는 레인지 시장, 높은 거래 빈도 선호",
        "entry_logic": [
            "**매수**: 가격이 하단 그리드 레벨에 도달",
            "**매도**: 가격이 상단 그리드 레벨에 도달",
            "그리드 간격 = ATR × 승수 (동적) 또는 고정 % 간격",
            "3-5개 그리드 라인 설정"
        ],
        "exit_logic": [
            "익절: 다음 그리드 레벨 (간격 거리)",
            "손절: 가격이 그리드 범위를 벗어남 (추세 감지)",
            "그리드 경계에서 청산하여 추세 손실 방지"
        ],
        "parameters": {
            "grid_lines": "그리드 레벨 수 (3-5)",
            "gap_percent": "그리드 간 기본 간격 (0.2-0.5%)",
            "atr_period": "ATR 계산 기간 (14)",
            "atr_multiplier": "동적 간격용 ATR 승수 (0.5-2.0)",
            "use_dynamic_gap": "ATR 기반 간격 vs 고정 % 사용",
            "stop_trigger_percent": "그리드 외부 손절 트리거 (1.0-3.0%)"
        },
        "strengths": [
            "횡보장에서 높은 수익성",
            "변동성에 자동 적응",
            "다중 진입점으로 리스크 분산"
        ],
        "weaknesses": [
            "추세장에서 반복 손실",
            "복잡한 포지션 관리",
            "강한 일방향 움직임에 취약"
        ]
    },
    {
        "code": "ST-05",
        "name": "MACD Momentum",
        "name_kr": "MACD 모멘텀",
        "type": "추세 추종",
        "description": "MACD 지표를 사용한 추세 추종 모멘텀 전략. MACD는 두 EMA 간의 관계를 측정하고 라인 교차와 히스토그램 변화를 통해 신호를 제공합니다.",
        "best_for": "추세가 있는 시장, 중기 모멘텀 움직임",
        "entry_logic": [
            "**롱**: MACD 라인이 시그널 라인을 상향 교차 (강세 교차)",
            "  AND MACD 히스토그램이 양수이며 증가",
            "**숏**: MACD 라인이 시그널 라인을 하향 교차 (약세 교차)",
            "  AND MACD 히스토그램이 음수이며 감소",
            "선택사항: 제로 라인 필터, 히스토그램 강도 필터"
        ],
        "exit_logic": [
            "반대 방향 MACD 교차",
            "손절/익절 달성",
            "시간 기반 청산: 최대 16시간 (MACD 추세는 지속될 수 있음)"
        ],
        "parameters": {
            "fast_period": "빠른 EMA 기간 (기본값: 12)",
            "slow_period": "느린 EMA 기간 (기본값: 26)",
            "signal_period": "시그널 라인 기간 (기본값: 9)",
            "use_zero_filter": "MACD 제로 라인으로 거래 필터링",
            "use_histogram_filter": "히스토그램 강도 요구",
            "histogram_threshold": "최소 히스토그램 값 (기본값: 0.0)"
        },
        "strengths": [
            "추세장에서 신뢰할 수 있는 신호",
            "모멘텀과 방향을 동시에 측정",
            "널리 사용되고 검증된 지표"
        ],
        "weaknesses": [
            "횡보장에서 허위 신호",
            "지연 지표 (후행)",
            "빠른 반전을 놓칠 수 있음"
        ]
    },
    {
        "code": "ST-06",
        "name": "Supertrend",
        "name_kr": "슈퍼트렌드",
        "type": "추세 추종",
        "description": "ATR 기반 추세 추종 지표로 명확한 시각적 신호 제공. 지표는 하락 추세에서 가격 위에(저항), 상승 추세에서 가격 아래에(지지) 표시됩니다.",
        "best_for": "강한 추세 시장, 명확한 방향성",
        "entry_logic": [
            "**롱**: 가격이 슈퍼트렌드를 상향 돌파 (추세 전환)",
            "**숏**: 가격이 슈퍼트렌드를 하향 돌파 (추세 전환)",
            "선택사항: EMA 필터로 추세 확인",
            "슈퍼트렌드 = (고가+저가)/2 ± (ATR × 승수)"
        ],
        "exit_logic": [
            "추세 전환 신호 (반대 방향 슈퍼트렌드 교차)",
            "손절/익절 (백업용)",
            "시간 기반 청산 없음 (추세가 계속 진행되도록 허용)"
        ],
        "parameters": {
            "atr_period": "ATR 계산 기간 (기본값: 10)",
            "atr_multiplier": "밴드용 ATR 승수 (기본값: 3.0)",
            "use_ema_filter": "EMA 추세 필터 추가",
            "ema_period": "추세 필터용 EMA 기간 (기본값: 50)",
            "stop_loss_percent": "손절매 비율 (기본값: 2.5%)",
            "take_profit_percent": "익절 비율 (기본값: 5.0%)"
        },
        "strengths": [
            "매우 명확한 추세 신호",
            "변동성에 자동 적응",
            "추세를 끝까지 추종",
            "심리적으로 따르기 쉬움"
        ],
        "weaknesses": [
            "횡보장에서 빈번한 전환",
            "진입 시점이 늦을 수 있음",
            "급격한 반전에 손실 발생"
        ]
    },
    {
        "code": "ST-07",
        "name": "Keltner Channel Reversion",
        "name_kr": "켈트너 채널 평균회귀",
        "type": "평균 회귀",
        "description": "ATR 기반 변동성 엔벨로프를 사용한 평균회귀 전략. 볼린저 밴드보다 부드럽고 휩쏘에 덜 취약합니다.",
        "best_for": "횡보 시장, 안정적인 변동성 구간",
        "entry_logic": [
            "**롱**: 가격이 하단 채널에 도달하거나 이탈 (과매도)",
            "  가격이 중간선으로 회귀할 것으로 예상",
            "**숏**: 가격이 상단 채널에 도달하거나 이탈 (과매수)",
            "  가격이 중간선으로 회귀할 것으로 예상",
            "선택사항: RSI 확인 필터"
        ],
        "exit_logic": [
            "목표: 가격이 중간선 (EMA)으로 회귀",
            "손절: 가격이 채널을 계속 벗어남 (추세 형성)",
            "시간 기반 청산: 최대 3시간 (빠른 회귀 예상)"
        ],
        "parameters": {
            "ema_period": "중간선 EMA 기간 (기본값: 20)",
            "atr_period": "ATR 계산 기간 (기본값: 10)",
            "atr_multiplier": "밴드용 ATR 승수 (기본값: 2.0)",
            "require_price_outside": "채널 밖에 가격이 있어야 진입",
            "use_rsi_filter": "RSI 확인 추가",
            "rsi_buy_threshold": "RSI 매수 수준 (기본값: 35)",
            "rsi_sell_threshold": "RSI 매도 수준 (기본값: 65)"
        },
        "strengths": [
            "볼린저 밴드보다 부드러움",
            "ATR 기반으로 변동성에 적응",
            "명확한 목표 (중간선)",
            "휩쏘 감소"
        ],
        "weaknesses": [
            "추세 돌파 시 손실",
            "평균회귀가 발생하지 않으면 실패",
            "강한 모멘텀에서 부적합"
        ]
    },
    {
        "code": "ST-08",
        "name": "Stochastic Momentum",
        "name_kr": "스토캐스틱 모멘텀",
        "type": "하이브리드",
        "description": "스토캐스틱 오실레이터를 사용하여 과매수/과매도 상태와 모멘텀 전환을 식별. %K와 %D 라인 교차를 통해 RSI와 다른 특성을 제공합니다.",
        "best_for": "중기 모멘텀 전환, 극단 구간에서의 반전",
        "entry_logic": [
            "**롱**: %K가 과매도 구간(<20-30)에서 %D를 상향 교차",
            "  과매도에서 강세로의 모멘텀 전환",
            "**숏**: %K가 과매수 구간(>70-80)에서 %D를 하향 교차",
            "  과매수에서 약세로의 모멘텀 전환",
            "선택사항: EMA 추세 필터, 다이버전스 감지"
        ],
        "exit_logic": [
            "반대 방향 교차 (주요 청산)",
            "손절/익절 달성",
            "시간 기반 청산: 최대 6시간 (모멘텀은 빠르게 진행)"
        ],
        "parameters": {
            "k_period": "%K 룩백 기간 (기본값: 14)",
            "k_smooth": "%K 스무딩 기간 (기본값: 3)",
            "d_period": "%D 스무딩 기간 (기본값: 3)",
            "oversold_level": "과매도 임계값 (기본값: 20)",
            "overbought_level": "과매수 임계값 (기본값: 80)",
            "use_trend_filter": "EMA 추세 필터 추가",
            "require_extreme_zone": "극단 구간에서만 거래 (기본값: True)"
        },
        "strengths": [
            "극단 구간에서 신뢰할 수 있는 신호",
            "RSI와 다른 관점 제공",
            "모멘텀 전환 조기 포착",
            "과매수/과매도 명확히 정의"
        ],
        "weaknesses": [
            "횡보장에서 잦은 교차",
            "강한 추세에서 조기 청산",
            "극단 구간이 오래 지속될 수 있음"
        ]
    }
]

# Display strategies based on filter
filtered_strategies = strategies
if strategy_type != "모든 전략":
    filtered_strategies = [s for s in strategies if s["type"] == strategy_type]

st.markdown(f"### 📖 전략 상세 설명 ({len(filtered_strategies)}개 전략)")
st.markdown("")

for strategy in filtered_strategies:
    with st.expander(f"**{strategy['code']}: {strategy['name']}** ({strategy['name_kr']}) - {strategy['type']}", expanded=False):

        # Header with type badge
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"#### {strategy['name']}")
            st.caption(f"**분류**: {strategy['type']} | **코드**: {strategy['code']}")
        with col2:
            if strategy['type'] == "추세 추종":
                st.info("📈 Trend Following")
            elif strategy['type'] == "평균 회귀":
                st.success("🔄 Mean Reversion")
            else:
                st.warning("⚡ Hybrid")

        st.markdown("---")

        # Description
        st.markdown("##### 📝 전략 개요")
        st.markdown(strategy['description'])
        st.markdown(f"**최적 시장 조건**: {strategy['best_for']}")

        st.markdown("")

        # Entry and Exit Logic
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 🟢 진입 로직")
            for logic in strategy['entry_logic']:
                st.markdown(f"- {logic}")

        with col2:
            st.markdown("##### 🔴 청산 로직")
            for logic in strategy['exit_logic']:
                st.markdown(f"- {logic}")

        st.markdown("---")

        # Parameters
        st.markdown("##### ⚙️ 주요 파라미터")

        param_data = []
        for param, desc in strategy['parameters'].items():
            param_data.append({
                "파라미터": f"`{param}`",
                "설명": desc
            })

        param_df = pd.DataFrame(param_data)
        st.dataframe(param_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Strengths and Weaknesses
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### ✅ 강점")
            for strength in strategy['strengths']:
                st.markdown(f"- {strength}")

        with col2:
            st.markdown("##### ⚠️ 약점")
            for weakness in strategy['weaknesses']:
                st.markdown(f"- {weakness}")

st.markdown("---")

# Strategy Selection Guide
st.markdown("### 🎯 전략 선택 가이드")

st.markdown("""
#### 시장 조건별 권장 전략

| 시장 상황 | 권장 전략 | 이유 |
|---------|---------|------|
| 🚀 **강한 상승 추세** | Supertrend, MACD Momentum | 추세를 끝까지 추종, 명확한 방향성 |
| 📉 **강한 하락 추세** | Volatility Breakout, Supertrend | 변동성 포착, 추세 반전 감지 |
| ↔️ **횡보 레인지** | RSI+Bollinger, Keltner Channel, Scalping Grid | 평균회귀 특성, 진동 수익 |
| ⚡ **높은 변동성** | Volatility Breakout, MACD Momentum | 변동성 확장 포착 |
| 💤 **낮은 변동성** | Scalping Grid, Keltner Channel | 작은 움직임에서도 수익 |
| 📊 **US 시장 개장** | Volatility Breakout, Volume MA Cross | 개장 시간대 최적화 |
| 🔀 **방향 불확실** | Stochastic Momentum, Scalping Grid | 양방향 대응 가능 |

#### 전략 조합 추천

**공격적 포트폴리오** (높은 수익, 높은 리스크):
- Volatility Breakout (40%)
- MACD Momentum (30%)
- Supertrend (30%)

**보수적 포트폴리오** (안정적 수익):
- RSI + Bollinger Reversion (35%)
- Keltner Channel Reversion (35%)
- Volume MA Cross (30%)

**균형 포트폴리오** (중간 리스크):
- Supertrend (25%)
- Volume MA Cross (25%)
- Keltner Channel Reversion (25%)
- Stochastic Momentum (25%)
""")

st.markdown("---")

# Meta-Strategy Explanation
st.markdown("### 🧠 메타 전략 시스템")

st.info("""
**"Static Strategy is Dead" - 동적 전략 선택의 철학**

이 시스템은 고정된 단일 전략을 사용하지 않습니다. 대신, 매일 다음 과정을 거칩니다:

1. **데이터 수집** (20:30-21:30): 최근 3-7일간의 시장 데이터 동기화
2. **전략 백테스팅** (21:30-22:20): 모든 전략과 파라미터 조합을 테스트
3. **성과 평가**: 각 전략의 수익률, 승률, MDD를 종합 점수로 계산
   - 종합 점수 = (총수익률 × 0.4) + (승률 × 0.3) + (1/|MDD| × 0.3)
4. **챔피언 선택**: 최고 점수의 전략과 파라미터를 당일 전략으로 선택
5. **실전 적용** (22:30-01:00): 선택된 전략으로 US 시장 개장 시간대 트레이딩

이 메타 전략 접근법으로 시장 조건 변화에 자동으로 적응하며,
각 전략이 가장 효과적인 시점에만 사용됩니다.
""")

st.markdown("---")

# Risk Management
st.markdown("### 🛡️ 리스크 관리 원칙")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 포지션 단위 리스크
    - 거래당 계좌의 1% 이하 리스크
    - 손절매 자동 설정
    - 레버리지 10배 (설정 가능)
    - 포지션 크기 = 리스크금액 / 손절거리
    """)

with col2:
    st.markdown("""
    #### 시스템 레벨 리스크
    - 일일 최대 손실 제한 (MAX_DAILY_LOSS_PERCENT)
    - 서킷 브레이커: 임계값 도달 시 거래 중단
    - 포지션 정리 시간: 01:00 (KST)
    - Telegram 실시간 알림
    """)

st.markdown("---")

# Footer
st.markdown("### 📚 추가 자료")

st.markdown("""
- **소스 코드**: `strategies/` 디렉토리에서 각 전략의 구현 확인
- **백테스팅**: Optimization 페이지에서 전략 성과 테스트
- **실시간 모니터링**: Dashboard 페이지에서 현재 포지션 추적
- **전략 선택 이력**: History 페이지에서 과거 선택 및 성과 확인
""")

st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
