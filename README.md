# US Market Volatility Hunter

고배율 레버리지 단타 매매 봇 - **전체 구현 완료** ✅

## 프로젝트 개요

미국 주식 시장 개장 시간에 맞춰 변동성이 극대화되는 시점에 최적의 전략을 동적으로 선정하여 암호화폐 선물 거래를 수행하는 자동매매 시스템입니다.

**핵심 철학:** "Static Strategy is Dead" - 고정된 전략이 아닌, 매일 백테스팅을 통해 검증된 '오늘의 챔피언 전략'을 선출하여 운용하는 메타 전략 시스템.

## 🎯 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                   Streamlit Dashboard                        │
│  (Real-time Monitoring & Control Interface)                 │
│  - Bot Control (Start/Stop/Restart)                         │
│  - Performance Monitoring                                    │
│  - Strategy Analysis                                         │
│  - Historical Data Visualization                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                Trading Bot Orchestrator                      │
│                   (main_bot.py)                              │
│                                                              │
│  Daily Workflow:                                             │
│  20:30 KST → Data Sync                                       │
│  21:30 KST → Strategy Selection (Daily Champion)            │
│  22:30 KST → Trading Session (Paper/Live)                   │
│  01:00 KST → Cleanup & Daily Report                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼───┐    ┌────▼────┐    ┌───▼────┐
│Selector│    │ Paper   │    │Executor│
│(Meta-  │    │Trader   │    │ (Live  │
│Strategy│    │(Virtual)│    │Trading)│
└───┬───┘    └────┬────┘    └───┬────┘
    │             │              │
    └─────────────┼──────────────┘
                  │
         ┌────────▼────────┐
         │   Backtester    │
         │   (Vectorized)  │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │   8 Strategies  │
         │  ST-01 ~ ST-08  │
         └────────┬────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
  ┌───▼──┐   ┌───▼──┐   ┌───▼──┐
  │Data  │   │ DB   │   │Telegram│
  │(CCXT)│   │(SQLite)   │Notifier│
  └──────┘   └──────┘   └────────┘
```

## Phase 4 완료 사항 (NEW! 🎉)

### ✅ Streamlit 대시보드 & 시스템 통합

1. **실시간 모니터링 대시보드** (`dashboard/pages/1_📊_Dashboard.py`)
   - 봇 상태 모니터링 (Running/Stopped)
   - **봇 제어**: Start, Stop, Restart 버튼
   - 실시간 성과 지표 (Balance, PNL, Win Rate)
   - 24시간 Equity Curve 차트
   - 현재 포지션 추적
   - 최근 거래 내역 (Last 10)
   - 시스템 헬스 (CPU, Memory, Uptime)
   - 30초 자동 새로고침

2. **오늘의 전략 페이지** (`dashboard/pages/2_🎯_Today_Strategy.py`)
   - 챔피언 전략 카드 (Score, Rank)
   - 성과 메트릭 그리드 (Return, Win Rate, Profit Factor, Sharpe, MDD)
   - 적용된 파라미터 테이블
   - 전략 랭킹 비교 (Top 10 Bar Chart)
   - 멀티 메트릭 레이더 차트
   - CSV 다운로드

3. **히스토리 & 분석 페이지** (`dashboard/pages/3_📈_History.py`)
   - 고급 필터링 (Date Range, Symbol, Strategy)
   - 누적 수익률 차트
   - 일별 PNL Bar Chart
   - Exit Reason 분포 (Pie Chart)
   - 페이지네이션 거래 로그 (50개/페이지)
   - 추가 분석 (Trade Duration, PNL Distribution, Strategy Breakdown)
   - CSV 다운로드

4. **최적화 뷰어 페이지** (`dashboard/pages/4_⚙️_Optimization.py`)
   - Optimization Run 선택기
   - Best Parameters 표시
   - 파라미터 탐색 (Contour Plot)
   - Score vs Parameter 시각화
   - 상세 백테스트 결과 테이블
   - CSV 다운로드

5. **고급 분석 페이지** (`dashboard/pages/5_🔬_Advanced_Analytics.py`)
   - 심화 통계 분석
   - 전략별 성과 비교
   - 리스크 메트릭 시각화

6. **전략 백과사전 페이지** (`dashboard/pages/6_📚_Strategies.py`)
   - 8가지 전략 상세 설명
   - 진입/청산 로직 문서화
   - 파라미터 가이드
   - 강점/약점 분석
   - 시장 조건별 권장 전략
   - 포트폴리오 조합 추천
   - 메타 전략 시스템 설명

7. **유틸리티 모듈** (`dashboard/utils/`)
   - **data_loader.py**: 데이터베이스 쿼리 레이어 (캐싱, Read-only 연결)
   - **bot_controller.py**: 봇 프로세스 관리 (PID 기반, Start/Stop/Status)
   - **formatters.py**: 데이터 포매팅 헬퍼 (Currency, Percentage, Timestamp)

8. **컴포넌트 모듈** (`dashboard/components/`)
   - **charts.py**: 9가지 Plotly 차트 (Equity Curve, Bar, Radar, Contour, Pie 등)
   - **metrics.py**: 메트릭 카드 컴포넌트
   - **tables.py**: 테이블 포맷터

9. **시스템 통합 개선**
   - 데이터베이스 WAL 모드 활성화 (동시 읽기/쓰기 지원)
   - Read-only 연결 메서드 추가
   - 봇 Graceful Shutdown (SIGTERM/SIGINT 핸들러)
   - PID 파일 관리 (프로세스 추적)

### 🚀 대시보드 실행 방법

```bash
# 대시보드 시작 (별도 터미널)
streamlit run dashboard/app.py

# 브라우저에서 자동으로 열림: http://localhost:8501
```

**대시보드에서 할 수 있는 작업:**
- ✅ 봇 시작/중지/재시작
- ✅ 실시간 성과 모니터링
- ✅ 오늘의 전략 확인
- ✅ 과거 거래 분석
- ✅ 최적화 결과 시각화
- ✅ CSV 데이터 다운로드

## Phase 3 완료 사항

### ✅ 메타 전략 시스템 & 페이퍼 트레이딩

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
   - Graceful Shutdown 지원

## Phase 2 완료 사항

### ✅ 전략 & 백테스팅 엔진

1. **벡터화된 백테스팅 엔진** (`modules/backtester.py`)
   - 고성능 pandas 기반 백테스팅
   - 레버리지, 수수료, 슬리피지 시뮬레이션
   - SL/TP 자동 실행 (intra-candle 시뮬레이션)
   - 종합 성과 지표 계산 (수익률, 승률, Profit Factor, MDD, Sharpe Ratio)
   - 복합 점수 계산

2. **8가지 트레이딩 전략 구현**
   - **ST-01: Volatility Breakout** - Larry Williams 변동성 돌파
   - **ST-02: RSI + Bollinger Reversion** - 평균 회귀 전략
   - **ST-03: Volume Weighted MA Cross** - 거래량 확인 MA 크로스
   - **ST-04: Dynamic Scalping Grid** - ATR 기반 동적 그리드
   - **ST-05: MACD Momentum** - 추세 추종 모멘텀
   - **ST-06: Supertrend** - ATR 기반 추세 지표
   - **ST-07: Keltner Channel Reversion** - 켈트너 채널 평균회귀
   - **ST-08: Stochastic Momentum** - 스토캐스틱 오실레이터

3. **Optuna 기반 파라미터 최적화** (`modules/optimizer.py`)
   - 베이지안 최적화
   - 제약 조건 설정
   - Grid Search 지원

## Phase 1 완료 사항

### ✅ 기반 구축

1. **CCXT 연동** (`modules/executor.py`) - 거래소 API 통합
2. **텔레그램 봇** (`modules/notifier.py`) - 실시간 알림 시스템
3. **데이터 수집기** (`modules/collector.py`) - OHLCV 데이터 관리
4. **기본 전략 클래스** (`strategies/base_strategy.py`) - 전략 인터페이스
5. **데이터베이스** (`database/init_db.py`) - SQLite 기반 데이터 관리

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 설정:

```bash
cp config/.env.example .env
```

`.env` 파일 예시:
```bash
# Exchange Configuration
EXCHANGE_NAME=binance
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Trading Configuration
TRADING_MODE=Paper                      # Paper 또는 Live
LEVERAGE=10
MAX_DAILY_LOSS_PERCENT=5.0

# Symbols
PRIMARY_SYMBOL=BTC/USDT
SECONDARY_SYMBOL=ETH/USDT

# Phase 3 Configuration
SELECTOR_MODE=quick                     # quick 또는 comprehensive
SELECTOR_LOOKBACK_DAYS=7
PAPER_TRADING_INITIAL_BALANCE=10000
PAPER_TRADING_POLL_INTERVAL=60
PAPER_TRADING_SESSION_DURATION=3.0
```

### 3. 데이터베이스 초기화

```bash
python database/init_db.py
```

## 사용 방법

### 🎯 권장 워크플로우

#### 1단계: 대시보드 시작
```bash
# 별도 터미널에서 실행
streamlit run dashboard/app.py
```

#### 2단계: 봇 실행 (두 가지 방법)

**방법 A: 대시보드에서 제어**
- 대시보드 접속 (`http://localhost:8501`)
- "Dashboard" 페이지에서 "START BOT" 버튼 클릭
- 실시간 모니터링

**방법 B: 터미널에서 실행**
```bash
# 전체 사이클 1회 실행 (테스트용)
python main_bot.py --mode once

# 스케줄러 모드 (자동 실행)
python main_bot.py --mode scheduled

# 개별 태스크 실행
python main_bot.py --mode sync      # 데이터 동기화만
python main_bot.py --mode select    # 전략 선정만
python main_bot.py --mode trade     # 트레이딩 세션만
python main_bot.py --mode cleanup   # 정리만
```

### 📊 대시보드 기능

| 페이지 | 기능 |
|--------|------|
| **Home** | 전체 시스템 개요, 퀵 스탯, 설정 정보 |
| **📊 Dashboard** | 실시간 모니터링, 봇 제어, 포지션 추적, 시스템 헬스 |
| **🎯 Today's Strategy** | 오늘의 챔피언 전략, 성과 메트릭, 파라미터, 랭킹 |
| **📈 History** | 과거 거래 분석, 필터링, 누적 수익, 통계 |
| **⚙️ Optimization** | 파라미터 최적화 결과, Contour Plot, 백테스트 리포트 |
| **🔬 Advanced Analytics** | 심화 통계 분석, 전략별 비교, 리스크 메트릭 |
| **📚 Strategies** | 8가지 전략 백과사전, 상세 가이드, 시장 조건별 추천 |

### 🧪 테스트 실행

```bash
# Phase 1 테스트
python test_phase1.py

# Phase 2 테스트
python tests/test_phase2.py

# Phase 3 테스트
python tests/test_phase3.py
```

### 📝 예제 스크립트

```bash
# 백테스팅 예제
python examples/example_backtest.py

# 파라미터 최적화 예제
python examples/example_optimization.py

# 일별 전략 선정 예제
python examples/example_daily_selection_phase3.py

# 페이퍼 트레이딩 예제
python examples/example_paper_trading_phase3.py
```

## 프로젝트 구조

```
claubit/
├── .streamlit/             # Streamlit 설정
│   └── config.toml
├── dashboard/              # 📊 Phase 4: Streamlit Dashboard
│   ├── __init__.py
│   ├── app.py             # 메인 엔트리 포인트
│   ├── pages/             # 멀티페이지 앱
│   │   ├── 1_📊_Dashboard.py      # 실시간 모니터링
│   │   ├── 2_🎯_Today_Strategy.py # 전략 표시
│   │   ├── 3_📈_History.py        # 히스토리 분석
│   │   ├── 4_⚙️_Optimization.py   # 최적화 뷰어
│   │   ├── 5_🔬_Advanced_Analytics.py # 고급 분석
│   │   └── 6_📚_Strategies.py     # 전략 백과사전
│   ├── components/        # UI 컴포넌트
│   │   ├── charts.py      # Plotly 차트
│   │   ├── metrics.py     # 메트릭 카드
│   │   └── tables.py      # 테이블 포맷터
│   └── utils/             # 유틸리티
│       ├── data_loader.py # DB 쿼리 레이어
│       ├── bot_controller.py # 봇 프로세스 관리
│       └── formatters.py  # 데이터 포맷팅
├── config/                 # 설정 파일
│   ├── config.py          # 설정 관리
│   └── .env.example       # 환경 변수 템플릿
├── data/                   # OHLCV 데이터 (Parquet)
├── database/               # SQLite 데이터베이스
│   └── init_db.py         # DB 초기화 및 관리
├── strategies/             # 전략 클래스
│   ├── base_strategy.py           # 기본 전략 클래스
│   ├── volatility_breakout.py     # ST-01: 변동성 돌파
│   ├── rsi_bollinger.py           # ST-02: RSI + 볼린저 평균회귀
│   ├── volume_ma_cross.py         # ST-03: 거래량 가중 MA 교차
│   ├── scalping_grid.py           # ST-04: 동적 스캘핑 그리드
│   ├── macd_momentum.py           # ST-05: MACD 모멘텀
│   ├── supertrend.py              # ST-06: 슈퍼트렌드
│   ├── keltner_channel.py         # ST-07: 켈트너 채널 평균회귀
│   └── stochastic_momentum.py     # ST-08: 스토캐스틱 모멘텀
├── modules/                # 핵심 기능 모듈
│   ├── collector.py       # 데이터 수집
│   ├── executor.py        # 주문 실행
│   ├── notifier.py        # 텔레그램 알림
│   ├── backtester.py      # 백테스팅 엔진
│   ├── optimizer.py       # Optuna 최적화
│   ├── selector.py        # 📍 Phase 3: 일별 전략 선정
│   └── paper_trader.py    # 📍 Phase 3: 페이퍼 트레이딩
├── tests/                  # 테스트 스크립트
│   ├── test_phase2.py
│   └── test_phase3.py
├── examples/               # 사용 예제
├── main_bot.py            # 📍 Phase 3: 메인 봇 오케스트레이터
├── requirements.txt        # Python 의존성
├── 기획문서.md             # 프로젝트 기획서
├── STRATEGIES.md          # 전략 상세 명세
├── CLAUDE.md              # AI 개발 가이드
├── PHASE4_COMPLETE.md     # Phase 4 완료 문서
└── README.md              # 프로젝트 문서
```

## 주요 기능

### 🤖 자동화된 일일 워크플로우
- 데이터 자동 동기화 (20:30 KST)
- AI 기반 전략 선정 (21:30 KST)
- 자동 트레이딩 실행 (22:30-01:00 KST)
- 일일 리포트 생성 (01:00+ KST)

### 📊 실시간 모니터링
- 웹 기반 대시보드
- 봇 원클릭 제어
- 실시간 성과 추적
- 시스템 헬스 모니터링

### 🎯 메타 전략 시스템
- 매일 최적 전략 자동 선정
- 8가지 전략 + 다양한 파라미터 조합
- 복합 점수 기반 랭킹
- Quick/Comprehensive 모드

### 💼 리스크 관리
- 자동 Stop Loss / Take Profit
- 서킷 브레이커 (일일 최대 손실)
- 레버리지 제어
- 포지션 사이징

### 📱 텔레그램 알림
- 거래 진입/청산 알림
- 일일 성과 리포트
- 에러 및 경고 알림
- 생존 신호 (Heartbeat)

## 개발 로드맵

- [x] **Phase 1: 기반 구축** ✅
  - CCXT 연동 및 주문 모듈
  - 텔레그램 봇 모듈
  - 데이터 수집기
  - 기본 전략 클래스
  - 데이터베이스 시스템

- [x] **Phase 2: 전략 및 백테스팅** ✅
  - 대표 전략 3종 구현
  - Vectorized Backtesting 엔진
  - Optuna 파라미터 최적화
  - 테스트 및 예제 스크립트

- [x] **Phase 3: 메타 전략 & 페이퍼 트레이딩** ✅
  - Daily Selector (전략 선정 자동화)
  - Paper Trading 시뮬레이터
  - 메인 봇 오케스트레이터
  - 자동화된 워크플로우

- [x] **Phase 4: Streamlit 대시보드** ✅
  - 실시간 모니터링 UI
  - 봇 제어 인터페이스
  - 성과 시각화
  - 최적화 결과 분석 도구

## 성능 특징

### ⚡ 고속 백테스팅
- Pandas 벡터화 연산
- 10만 캔들 < 1초 처리
- 병렬 최적화 지원

### 💾 효율적인 데이터 관리
- Parquet 압축 저장
- SQLite WAL 모드 (동시 접근)
- 캐싱 시스템 (Streamlit)

### 🔒 안전성
- Paper Trading 우선 테스트
- 서킷 브레이커
- Graceful Shutdown
- 에러 복구 메커니즘

## 기술 스택

| 카테고리 | 기술 |
|----------|------|
| **Language** | Python 3.9+ |
| **Exchange API** | CCXT |
| **Data Processing** | Pandas, NumPy |
| **Database** | SQLite (WAL mode) |
| **Optimization** | Optuna |
| **Visualization** | Plotly, Streamlit |
| **Scheduling** | APScheduler |
| **Notification** | python-telegram-bot |
| **Configuration** | python-dotenv |

## 주의사항

### ⚠️ 실거래 전 필독

1. **Paper Trading 테스트 필수**
   - 최소 1주일 이상 Paper Trading으로 검증
   - 다양한 시장 상황에서 테스트
   - 모든 기능이 정상 작동하는지 확인

2. **리스크 관리**
   - 초기에는 소액으로 시작
   - 일일 최대 손실 한도 설정 (`MAX_DAILY_LOSS_PERCENT`)
   - 과도한 레버리지 지양
   - 포트폴리오의 일부만 투자

3. **보안**
   - API 키 절대 공개 금지
   - `.env` 파일 git ignore 확인
   - Read-only API 권한 사용 권장 (테스트 시)
   - 2FA 활성화

4. **모니터링**
   - 대시보드로 실시간 모니터링
   - 텔레그램 알림 설정
   - 정기적인 로그 확인
   - 서킷 브레이커 동작 확인

5. **법적 책임**
   - 이 프로젝트는 교육 목적입니다
   - 실거래로 인한 손실은 사용자 책임
   - 해당 지역의 금융 규제 확인

## 문제 해결

### 대시보드가 실행되지 않는 경우
```bash
# Streamlit 재설치
pip install --upgrade streamlit streamlit-autorefresh

# 포트 변경
streamlit run dashboard/app.py --server.port 8502
```

### 봇이 시작되지 않는 경우
```bash
# 설정 확인
python config/config.py

# 데이터베이스 리셋
python database/init_db.py --reset

# 로그 확인
python main_bot.py --mode once  # 터미널에서 직접 실행
```

### 데이터베이스 락 오류
```bash
# WAL 모드 확인
python -c "from database.init_db import DatabaseManager; db = DatabaseManager(); db.initialize_database()"
```

## 기여 및 지원

- GitHub Issues: 버그 리포트 및 기능 제안
- 개인 프로젝트로 운영 중

## 라이선스

개인 프로젝트용 - 상업적 사용 제한

---

**⚡ 개발 완료!** 모든 Phase가 구현되었습니다. Paper Trading으로 충분히 테스트한 후 실거래를 시작하세요!
