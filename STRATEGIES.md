# 📊 Bitcoin High-Leverage Day Trading Strategies

이 문서는 비트코인(BTC) 선물 거래를 위한 4가지 핵심 전략의 로직, 진입/청산 조건, 그리고 최적화 가능한 파라미터(Hyper-parameters)를 정의합니다.

## 0. 전략 요약 (Strategy Summary)

| 전략 ID | 전략 명 (Name) | 유형 (Type) | 시장 상황 (Market Condition) | 리스크 (Risk) |
| :--- | :--- | :--- | :--- | :--- |
| **ST-01** | **Volatility Breakout** | 추세 추종 (Trend) | 강한 상승/하락장, 변동성 확대 시 | Medium |
| **ST-02** | **RSI + Bollinger Reversion** | 역추세 (Mean Reversion) | 횡보장 (Box pattern), 박스권 | High (역추세 위험) |
| **ST-03** | **Volume Weighted MA Cross** | 추세 추종 (Trend) | 거래량이 동반된 추세장 | Low/Medium |
| **ST-04** | **Dynamic Scalping Grid** | 변동성 매매 (Neutral) | 방향성 없는 급등락장 | High (물림 위험) |

---

## 1. ST-01: 변동성 돌파 전략 (Modified Volatility Breakout)

래리 윌리엄스(Larry Williams)의 전설적인 전략을 단타에 맞게 수정한 버전입니다. 미국 장 시작 시점의 변동성을 이용해 추세가 터지는 방향으로 탑승합니다.

### ⚙️ 알고리즘 로직
1.  **Range 계산**: 전일(또는 직전 세션)의 고가($H_{prev}$)와 저가($L_{prev}$)의 차이를 구합니다.
    $$Range = H_{prev} - L_{prev}$$
2.  **매수 진입 (Long Entry)**: 현재가가 `당일 시가 + (Range * k)`를 돌파할 때 매수.
3.  **매도 진입 (Short Entry)**: 현재가가 `당일 시가 - (Range * k)`를 하향 돌파할 때 매도.
4.  **필터링 (Noise Filter)**: 이동평균선(MA) 위에 있을 때만 Long, 아래 있을 때만 Short (선택 사항).

### 🎯 진입 및 청산 조건
* **Long Condition**: $Price_{current} > Open_{day} + (Range \times k)$
* **Short Condition**: $Price_{current} < Open_{day} - (Range \times k)$
* **Exit Condition**:
    * **Time Cut**: 장 마감 시간(06:00 KST)에 전량 청산.
    * **Stop Loss**: 진입가 대비 -N% 도달 시 손절.

### 🔧 최적화 파라미터 (Optimizing Params)
* **`k` (Noise Ratio)**: 0.3 ~ 0.8 (Step 0.1). *값이 작을수록 진입이 빠르지만 휩소(속임수) 가능성 높음.*
* **`Lookback Period`**: Range 계산 기준 시간 (예: 24시간, 12시간, 4시간).
* **`MA Filter`**: 추세 필터용 이평선 기간 (예: 5일, 20일).

---

## 2. ST-02: RSI & 볼린저 밴드 역추세 (RSI + BB Reversion)

가격이 지나치게 올랐거나 내렸을 때, 평균으로 회귀하려는 성질을 이용한 전략입니다. 횡보장에서 승률이 매우 높습니다.

### ⚙️ 알고리즘 로직
1.  **지표 계산**: RSI(14), 볼린저 밴드(20, 2) 계산.
2.  **과매도(Oversold) 판단**: 가격이 밴드 하단을 뚫고 내려갔으며, RSI가 30 미만일 때.
3.  **과매수(Overbought) 판단**: 가격이 밴드 상단을 뚫고 올라갔으며, RSI가 70 초과일 때.

### 🎯 진입 및 청산 조건
* **Long Entry**: $Price < Band_{lower}$ AND $RSI < RSI_{buy\_threshold}$
* **Short Entry**: $Price > Band_{upper}$ AND $RSI > RSI_{sell\_threshold}$
* **Take Profit (익절)**: 가격이 볼린저 밴드 중심선(SMA 20)에 도달했을 때.
* **Stop Loss (손절)**: 밴드 폭(Width)의 N% 만큼 더 밀렸을 때 강제 청산.

### 🔧 최적화 파라미터 (Optimizing Params)
* **`RSI Period`**: 9 ~ 21 (기본 14).
* **`RSI Threshold`**: 매수(20~35), 매도(65~80).
* **`BB StdDev`**: 볼린저 밴드 표준편차 승수 (1.8 ~ 2.5).

---

## 3. ST-03: 거래량 가중 이평선 크로스 (Volume Weighted MA Cross)

단순히 골든크로스만 보는 것이 아니라, **"거래량이 터지면서"** 크로스가 발생한 신뢰도 높은 신호만 잡습니다. 휩소(거짓 신호)를 줄이는 데 집중합니다.

### ⚙️ 알고리즘 로직
1.  단기 이평선(Short MA)과 장기 이평선(Long MA)을 계산.
2.  현재 캔들의 거래량($Vol_{current}$)이 지난 N개 캔들 평균 거래량($Vol_{avg}$)보다 M배 이상인지 확인.

### 🎯 진입 및 청산 조건
* **Long Entry**:
    * $MA_{short}$ crosses over $MA_{long}$
    * AND $Vol_{current} > Vol_{avg} \times Vol_{multiplier}$
* **Short Entry**:
    * $MA_{short}$ crosses under $MA_{long}$
    * AND $Vol_{current} > Vol_{avg} \times Vol_{multiplier}$
* **Exit Condition**: 반대 시그널 발생 시 또는 Trailing Stop 발동 시.

### 🔧 최적화 파라미터 (Optimizing Params)
* **`Short Window`**: 5 ~ 20분.
* **`Long Window`**: 20 ~ 60분.
* **`Vol Multiplier`**: 1.2 ~ 3.0 (거래량이 평소의 몇 배여야 하는가).

---

## 4. ST-04: 다이내믹 스캘핑 그리드 (Dynamic Scalping Grid)

지정된 범위 내에 촘촘하게 그물을 쳐서, 시세가 위아래로 흔들릴 때마다 수익을 쌓는 전략입니다. 고레버리지 사용 시 매우 위험할 수 있으므로 **손절 라인(Stop Loss)을 매우 타이트하게 설정**해야 합니다.

### ⚙️ 알고리즘 로직
1.  현재 가격을 기준으로 위로 N개(매도 주문), 아래로 N개(매수 주문)의 지정가 주문을 미리 계산.
2.  각 그리드(Grid)의 간격은 변동성(ATR)에 비례하여 설정 (변동성이 크면 간격을 넓힘).

### 🎯 진입 및 청산 조건
* **Setup**: 현재가 $P$ 기준.
    * Buy Limit 1: $P - (Gap \times 1)$, Take Profit: $P$
    * Buy Limit 2: $P - (Gap \times 2)$, Take Profit: $P - (Gap \times 1)$
* **Stop Loss (필수)**: 가격이 특정 범위를 벗어나 추세가 형성되면 모든 그리드 주문 취소 및 일괄 손절.

### 🔧 최적화 파라미터 (Optimizing Params)
* **`Grid Lines`**: 주문 개수 (예: 위아래 각 3개).
* **`Gap %`**: 그리드 간 간격 (예: 0.2% ~ 0.5%).
* **`Stop Trigger`**: 그리드 범위를 몇 % 벗어나면 손절할 것인가.

---

## 🏆 Daily Optimization Logic (매일 아침 수행)

프로그램은 매일 **미국장 시작 1시간 전**에 다음 로직을 수행하여 `Best Strategy`를 선정합니다.

1.  **데이터 로드**: 최근 14일간의 15분봉/1시간봉 데이터.
2.  **전수 조사 (Grid Search)**:
    * 위 4개 전략에 대해 모든 파라미터 조합을 시뮬레이션.
    * 예: ST-01의 `k`값을 0.4, 0.5, 0.6으로 변경해가며 테스트.
3.  **스코어링 (Scoring Formula)**:
    $$Score = (TotalReturn \times 0.4) + (WinRate \times 0.3) + (\frac{1}{|MDD|} \times 0.3)$$
    * *수익률이 높고, 승률이 좋으며, 최대 낙폭(MDD)이 적은 전략에 가산점.*
4.  **최종 선택**: 점수가 가장 높은 **단 하나의 전략과 파라미터**를 그날의 트레이딩 로직으로 탑재.
