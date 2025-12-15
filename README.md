# US Market Volatility Hunter

고배율 레버리지 단타 매매 봇 - Phase 1 구현 완료

## 프로젝트 개요

미국 주식 시장 개장 시간에 맞춰 변동성이 극대화되는 시점에 최적의 전략을 동적으로 선정하여 암호화폐 선물 거래를 수행하는 자동매매 시스템입니다.

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

## 프로젝트 구조

```
claubit/
├── config/                 # 설정 파일
│   ├── __init__.py
│   ├── config.py          # 설정 관리
│   └── .env.example       # 환경 변수 템플릿
├── data/                   # OHLCV 데이터 저장
├── database/               # SQLite 데이터베이스
│   └── init_db.py         # DB 초기화 스크립트
├── strategies/             # 전략 클래스
│   ├── __init__.py
│   └── base_strategy.py   # 기본 전략 클래스
├── modules/                # 핵심 기능 모듈
│   ├── __init__.py
│   ├── collector.py       # 데이터 수집
│   ├── executor.py        # 주문 실행
│   └── notifier.py        # 텔레그램 알림
├── requirements.txt        # Python 의존성
└── README.md              # 프로젝트 문서
```

## 다음 단계 (Phase 2)

- [ ] 대표 전략 3종 구현
- [ ] Vectorized Backtesting 엔진
- [ ] Optuna 연동 및 파라미터 최적화

## 주의사항

⚠️ **실제 거래 전 반드시 Paper Trading으로 충분히 테스트하세요!**

- 현재는 Phase 1 단계로 기본 모듈만 구현되었습니다.
- 실제 거래는 Phase 4 완료 후 진행하는 것을 권장합니다.
- API 키는 절대 공개하지 마세요.

## 라이선스

개인 프로젝트용
