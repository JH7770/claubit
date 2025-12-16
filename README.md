# US Market Volatility Hunter

고배율 레버리지 단타 매매 봇 - **Phase 3 구현 완료** ✅

## 프로젝트 개요

미국 주식 시장 개장 시간에 맞춰 변동성이 극대화되는 시점에 최적의 전략을 동적으로 선정하여 암호화폐 선물 거래를 수행하는 자동매매 시스템입니다.

**핵심 철학:** "Static Strategy is Dead" - 고정된 전략이 아닌, 매일 백테스팅을 통해 검증된 '오늘의 챔피언 전략'을 선출하여 운용하는 메타 전략 시스템.

## Phase 3 완료 사항 (NEW!)

### ✅ 구현된 기능

1. **일별 전략 선정기** (`modules/selector.py`)
   - 메타 전략 선정 프로세스 자동화
   - **Quick Mode**: 사전 정의된 파라미터 세트 테스트 (5-10분)
   - **Comprehensive Mode**: Optuna 최적화 수행 (20-30분)
   - 최근 7일 데이터로 백테스팅
   - 복합 점수로 전략 랭킹
   - 선정 결과 데이터베이스 저장
   - 텔레그램 알림 발송

2. **페이퍼 트레이딩 시뮬레이터** (`modules/paper_trader.py`)
   - 실제 주문 없이 실시간 거래 시뮬레이션
   - 가상 포트폴리오 관리 (잔고, 포지션, 자본금)
   - 자동 SL/TP 트리거
   - 서킷 브레이커 (일일 최대 손실 제한)
   - 실시간 성과 추적
   - 전략 시그널 자동 실행
   - 거래 내역 데이터베이스 저장
   - 텔레그램 알림 통합

3. **메인 봇 오케스트레이터** (`main_bot.py`)
   - 일일 워크플로우 자동화
   - **20:30-21:30 KST**: 데이터 동기화
   - **21:30-22:20 KST**: 일별 전략 선정
   - **22:30-01:00 KST**: 트레이딩 세션 실행
   - **01:00+ KST**: 포지션 정리 및 일일 리포트
   - APScheduler 통합 (자동 스케줄링)
   - 명령줄 인터페이스 지원

4. **데이터베이스 확장**
   - `paper_trading` 플래그 추가 (trade_history 테이블)
   - 페이퍼/라이브 거래 구분 기록

5. **설정 확장** (`config/config.py`)
   - 전략 선정 모드 설정 (quick/comprehensive)
   - 페이퍼 트레이딩 설정 (초기 잔고, 폴링 간격 등)
   - 일일 최대 손실 퍼센트 설정

6. **테스트 및 예제**
   - Phase 3 통합 테스트 (`tests/test_phase3.py`)
     - 15개 테스트 케이스
     - 전략 선정기 및 페이퍼 트레이더 검증
   - 일별 전략 선정 예제 (`examples/example_daily_selection_phase3.py`)
   - 페이퍼 트레이딩 예제 (`examples/example_paper_trading_phase3.py`)

### 🚀 사용 방법 (Phase 3)

#### 전략 선정 (수동)
```bash
# Quick 모드로 전략 선정
python -m modules.selector

# 또는 예제 스크립트 실행
python examples/example_daily_selection_phase3.py
```

#### 페이퍼 트레이딩 (수동)
```bash
# 페이퍼 트레이딩 테스트
python examples/example_paper_trading_phase3.py
```

#### 전체 봇 실행
```bash
# 전체 사이클 1회 실행 (테스트용)
python main_bot.py --mode once

# 개별 태스크 실행
python main_bot.py --mode sync      # 데이터 동기화만
python main_bot.py --mode select    # 전략 선정만
python main_bot.py --mode trade     # 트레이딩 세션만
python main_bot.py --mode cleanup   # 정리만

# 스케줄러 모드 (자동 실행)
python main_bot.py --mode scheduled
```

#### 설정 (.env 파일)
```bash
# Phase 3 추가 설정
SELECTOR_MODE=quick                    # quick 또는 comprehensive
SELECTOR_LOOKBACK_DAYS=7               # 백테스팅 기간
SELECTOR_MIN_TRADES=10                 # 최소 거래 수
PAPER_TRADING_INITIAL_BALANCE=10000    # 페이퍼 트레이딩 초기 잔고
PAPER_TRADING_POLL_INTERVAL=60         # 폴링 간격 (초)
PAPER_TRADING_SESSION_DURATION=3.0     # 세션 길이 (시간)
```

## Phase 2 완료 사항

### ✅ 구현된 기능

1. **벡터화된 백테스팅 엔진** (`modules/backtester.py`)
   - 고성능 pandas 기반 백테스팅
   - 레버리지, 수수료, 슬리피지 시뮬레이션
   - SL/TP 자동 실행 (intra-candle 시뮬레이션)
   - 종합 성과 지표 계산 (수익률, 승률, Profit Factor, MDD, Sharpe Ratio)
   - 복합 점수 계산 (기획문서 공식 적용)

2. **3가지 핵심 전략 구현**
   - **ST-01: Volatility Breakout** (`strategies/volatility_breakout.py`)
     - Larry Williams 변동성 돌파 전략
     - 파라미터: k (noise ratio), lookback_period, MA filter
   - **ST-02: RSI + Bollinger Reversion** (`strategies/rsi_bollinger.py`)
     - RSI와 볼린저 밴드를 활용한 평균 회귀 전략
     - 횡보장에 최적화
   - **ST-03: Volume Weighted MA Cross** (`strategies/volume_ma_cross.py`)
     - 거래량 확인이 포함된 이동평균 크로스오버
     - 신뢰도 높은 신호만 거래

3. **Optuna 기반 파라미터 최적화** (`modules/optimizer.py`)
   - 베이지안 최적화를 통한 하이퍼파라미터 탐색
   - 제약 조건 설정 (최소 거래 수, 최대 낙폭)
   - Grid Search 지원
   - 최적화 결과 데이터베이스 저장

4. **데이터베이스 확장**
   - `optimization_runs` 테이블 추가
   - 백테스트 결과 저장/조회 메서드
   - 날짜별 최적 전략 조회

5. **테스트 및 예제 스크립트**
   - Phase 2 통합 테스트 (`tests/test_phase2.py`)
   - 백테스팅 예제 (`examples/example_backtest.py`)
   - 최적화 예제 (`examples/example_optimization.py`)
   - 일별 전략 선정 시뮬레이션 (`examples/daily_strategy_selection.py`)

## Phase 1 완료 사항

### ✅ 구현된 기능

1. **프로젝트 구조 설정**
   - 모듈화된 폴더 구조 생성
   - 설정 파일 시스템 구축

2. **CCXT 연동 및 주문 모듈** (`modules/executor.py`)
   - 거래소 연동 (Binance Futures)
   - 시장가/지정가 주문 실행
   - 포지션 관리 (진입/청산)
   - Stop Loss / Take Profit 설정
   - 레버리지 설정
   - 잔고 조회

3. **텔레그램 봇 모듈** (`modules/notifier.py`)
   - 매매 알림 (진입/청산)
   - 일일 리포트
   - 에러 알림
   - 생존 신호 (Heartbeat)
   - 전략 선정 알림
   - 리스크 경고

4. **데이터 수집기** (`modules/collector.py`)
   - OHLCV 데이터 다운로드
   - 과거 데이터 저장 (Parquet 형식)
   - 데이터 업데이트
   - 실시간 가격 조회
   - 호가창 데이터 조회

5. **기본 전략 클래스** (`strategies/base_strategy.py`)
   - 추상 베이스 클래스 정의
   - 시그널 생성 인터페이스
   - 포지션 사이징
   - SL/TP 계산
   - 예제 전략: SMA Cross

6. **데이터베이스 시스템** (`database/init_db.py`)
   - SQLite 데이터베이스 설정
   - 전략 풀 관리
   - 백테스트 결과 저장
   - 거래 내역 기록
   - 일별 요약 통계

## 설치 방법

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 실제 API 키를 입력하세요:

```bash
cp config/.env.example .env
```

`.env` 파일 수정:
```
EXCHANGE_NAME=binance
API_KEY=your_actual_api_key
API_SECRET=your_actual_api_secret
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### 3. 데이터베이스 초기화

```bash
python database/init_db.py
```

## 사용 방법

### 데이터 수집 테스트

```bash
python -c "from modules.collector import DataCollector; collector = DataCollector('binance'); collector.download_historical_data('BTC/USDT', '1m', days=1)"
```

### 설정 확인

```bash
python config/config.py
```

### 데이터베이스 리셋 (모든 데이터 삭제 후 재생성)

```bash
python database/init_db.py --reset
```

### Phase 2 테스트 실행

```bash
# Phase 2 통합 테스트
python tests/test_phase2.py

# 백테스팅 예제
python examples/example_backtest.py

# 파라미터 최적화 예제
python examples/example_optimization.py

# 일별 전략 선정 시뮬레이션
python examples/daily_strategy_selection.py
```

### 백테스팅 사용 예제

```python
from modules import VectorizedBacktester
from strategies import VolatilityBreakoutStrategy
import pandas as pd

# 데이터 로드
df = pd.read_parquet('data/BTCUSDT_1m.parquet')

# 전략 초기화
strategy = VolatilityBreakoutStrategy(params={
    'k': 0.5,
    'lookback_period': 24
})

# 백테스팅 실행
backtester = VectorizedBacktester(initial_balance=10000, leverage=10)
results = backtester.run_backtest(df, strategy)

# 결과 출력
print(f"Total Return: {results['total_return']:.2f}%")
print(f"Win Rate: {results['win_rate']:.2f}%")
print(f"Composite Score: {results['score']:.2f}")
```

### 파라미터 최적화 사용 예제

```python
from modules import VectorizedBacktester, StrategyOptimizer
from strategies import VolatilityBreakoutStrategy

# 최적화 실행
backtester = VectorizedBacktester(initial_balance=10000, leverage=10)
optimizer = StrategyOptimizer(backtester)

param_space = {
    'k': {'type': 'float', 'low': 0.3, 'high': 0.8, 'step': 0.1},
    'lookback_period': {'type': 'categorical', 'choices': [12, 24, 48]}
}

best_params, trials_df = optimizer.optimize_strategy(
    strategy_class=VolatilityBreakoutStrategy,
    df=df,
    param_space=param_space,
    n_trials=50,
    objective_metric='score'
)

print(f"Best parameters: {best_params}")
```

## 프로젝트 구조

```
claubit/
├── config/                 # 설정 파일
│   ├── __init__.py
│   ├── config.py          # 설정 관리
│   └── .env.example       # 환경 변수 템플릿
├── data/                   # OHLCV 데이터 저장
├── database/               # SQLite 데이터베이스
│   └── init_db.py         # DB 초기화 및 관리
├── strategies/             # 전략 클래스
│   ├── __init__.py
│   ├── base_strategy.py   # 기본 전략 클래스
│   ├── volatility_breakout.py  # ST-01 전략
│   ├── rsi_bollinger.py        # ST-02 전략
│   └── volume_ma_cross.py      # ST-03 전략
├── modules/                # 핵심 기능 모듈
│   ├── __init__.py
│   ├── collector.py       # 데이터 수집
│   ├── executor.py        # 주문 실행
│   ├── notifier.py        # 텔레그램 알림
│   ├── backtester.py      # 백테스팅 엔진
│   └── optimizer.py       # Optuna 최적화
├── tests/                  # 테스트 스크립트
│   └── test_phase2.py     # Phase 2 통합 테스트
├── examples/               # 사용 예제
│   ├── example_backtest.py
│   ├── example_optimization.py
│   └── daily_strategy_selection.py
├── requirements.txt        # Python 의존성
├── 기획문서.md             # 프로젝트 기획서
├── STRATEGIES.md          # 전략 상세 명세
└── README.md              # 프로젝트 문서
```

## 개발 로드맵

- [x] **Phase 1: 기반 구축** ✅
  - CCXT 연동 및 주문 모듈
  - 텔레그램 봇 모듈
  - 데이터 수집기
  - 기본 전략 클래스
  - 데이터베이스 시스템

- [x] **Phase 2: 전략 및 백테스팅** ✅
  - 대표 전략 3종 구현 (ST-01, ST-02, ST-03)
  - Vectorized Backtesting 엔진
  - Optuna 연동 및 파라미터 최적화
  - 테스트 및 예제 스크립트

- [ ] **Phase 3: Meta-Strategy 로직** (다음 단계)
  - Daily Selector (오늘의 전략 선정 자동화)
  - Paper Trading 시뮬레이터
  - 전략 성과 비교 및 랭킹

- [ ] **Phase 4: Streamlit 대시보드**
  - 실시간 모니터링 UI
  - 백테스팅 결과 시각화
  - 최적화 결과 분석 도구
  - 시스템 제어 인터페이스

## 주의사항

⚠️ **실제 거래 전 반드시 Paper Trading으로 충분히 테스트하세요!**

- 현재는 Phase 1 단계로 기본 모듈만 구현되었습니다.
- 실제 거래는 Phase 4 완료 후 진행하는 것을 권장합니다.
- API 키는 절대 공개하지 마세요.

## 라이선스

개인 프로젝트용
