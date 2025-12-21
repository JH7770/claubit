# Design System

변동성 헌터 대시보드의 중앙 집중식 디자인 시스템입니다. 일관된 UI/UX를 위한 색상, 타이포그래피, 간격 등의 디자인 토큰을 제공합니다.

## 📁 구조

```
design_system/
├── __init__.py          # 패키지 진입점
├── colors.py            # 색상 팔레트 (Tailwind 기반)
├── typography.py        # 폰트 크기, 굵기, 행간
├── spacing.py           # 여백, 패딩, 그림자, z-index
├── tokens.py            # 통합 디자인 토큰
└── README.md            # 이 파일
```

## 🎨 사용 방법

### 기본 사용

```python
from dashboard.design_system import DesignTokens as DT

# 색상 사용
primary_color = DT.COLOR_PRIMARY  # '#3B82F6'
success_color = DT.COLOR_SUCCESS  # '#10B981'

# 타이포그래피 사용
title_size = DT.FONT_SIZE_H1      # 32px
body_size = DT.FONT_SIZE_BODY     # 16px

# 간격 사용
padding = DT.SPACE_4              # 16px
margin = DT.SPACE_6               # 24px
```

### 테마별 색상 (라이트/다크 모드)

```python
from dashboard.design_system import Colors

# 라이트 모드 색상
bg_light = Colors.get_bg_primary(dark_mode=False)
text_light = Colors.get_text_primary(dark_mode=False)

# 다크 모드 색상
bg_dark = Colors.get_bg_primary(dark_mode=True)
text_dark = Colors.get_text_primary(dark_mode=True)

# 트레이딩 색상
profit_color = Colors.get_profit_color(dark_mode=False)
loss_color = Colors.get_loss_color(dark_mode=False)
```

### 차트에서 사용

```python
from dashboard.components.charts import ChartBuilder

# ChartBuilder는 이미 디자인 시스템을 사용합니다
chart = ChartBuilder.equity_curve(
    df=data,
    dark_mode=True  # 다크 모드 색상 자동 적용
)
```

### 컴포넌트 스타일링

```python
from dashboard.design_system import DesignTokens as DT

# 메트릭 카드 스타일
card_style = DT.get_metric_card_style(dark_mode=False)
# Returns:
# {
#     'background-color': '#ffffff',
#     'border': '1px solid #e5e7eb',
#     'border-radius': '12px',
#     'padding': '24px',
#     'box-shadow': '0 4px 6px -1px rgba(0, 0, 0, 0.1), ...'
# }

# 버튼 스타일
primary_btn = DT.get_button_style(variant='primary')
danger_btn = DT.get_button_style(variant='danger')
```

## 🎨 색상 팔레트

### 주요 색상

| 색상 | Light | Dark | 용도 |
|------|-------|------|------|
| Primary | `#3B82F6` | `#60A5FA` | 주요 액션, 링크 |
| Success | `#10B981` | `#34D399` | 성공, 수익 |
| Warning | `#F59E0B` | `#FBBF24` | 경고, 주의 |
| Error | `#EF4444` | `#F87171` | 오류, 손실 |

### 트레이딩 전용 색상

- **수익**: `Colors.PROFIT_LIGHT` / `Colors.PROFIT_DARK`
- **손실**: `Colors.LOSS_LIGHT` / `Colors.LOSS_DARK`
- **롱 포지션**: `Colors.LONG_COLOR` (`#3B82F6`)
- **숏 포지션**: `Colors.SHORT_COLOR` (`#F59E0B`)

### 순위 색상

- **금메달**: `Colors.GOLD` (`#FFD700`)
- **은메달**: `Colors.SILVER` (`#C0C0C0`)
- **동메달**: `Colors.BRONZE` (`#CD7F32`)

## 📐 타이포그래피

### 제목 크기

```python
Typography.FONT_SIZE_H1  # 32px
Typography.FONT_SIZE_H2  # 28px
Typography.FONT_SIZE_H3  # 24px
Typography.FONT_SIZE_H4  # 20px
Typography.FONT_SIZE_H5  # 18px
Typography.FONT_SIZE_H6  # 16px
```

### 본문 크기

```python
Typography.FONT_SIZE_BODY_LARGE  # 18px
Typography.FONT_SIZE_BODY        # 16px
Typography.FONT_SIZE_BODY_SMALL  # 14px
Typography.FONT_SIZE_CAPTION     # 12px
```

### 굵기

```python
Typography.FONT_WEIGHT_LIGHT      # 300
Typography.FONT_WEIGHT_REGULAR    # 400
Typography.FONT_WEIGHT_MEDIUM     # 500
Typography.FONT_WEIGHT_SEMIBOLD   # 600
Typography.FONT_WEIGHT_BOLD       # 700
```

### 텍스트 스타일 프리셋

```python
h1_style = Typography.get_h1_style()
# Returns: {'font-size': '32px', 'font-weight': 700, 'line-height': 1.2, ...}

body_style = Typography.get_body_style()
button_style = Typography.get_button_style()
metric_style = Typography.get_metric_value_style()
```

## 📏 Spacing

### 기본 스케일 (8px 베이스)

```python
Spacing.SPACE_1   # 4px
Spacing.SPACE_2   # 8px
Spacing.SPACE_3   # 12px
Spacing.SPACE_4   # 16px
Spacing.SPACE_6   # 24px
Spacing.SPACE_8   # 32px
Spacing.SPACE_12  # 48px
Spacing.SPACE_16  # 64px
```

### Border Radius

```python
Spacing.RADIUS_SMALL   # 4px
Spacing.RADIUS_MEDIUM  # 8px
Spacing.RADIUS_LARGE   # 12px
Spacing.RADIUS_XLARGE  # 16px
Spacing.RADIUS_FULL    # 9999px (원형)
```

### 그림자

```python
Spacing.SHADOW_SMALL   # 미세한 그림자
Spacing.SHADOW_MEDIUM  # 중간 그림자
Spacing.SHADOW_LARGE   # 큰 그림자
Spacing.SHADOW_CARD    # 카드용 그림자
```

### Z-Index 레이어

```python
Spacing.Z_INDEX_DROPDOWN       # 1000
Spacing.Z_INDEX_MODAL_BACKDROP # 1200
Spacing.Z_INDEX_MODAL          # 1300
Spacing.Z_INDEX_TOOLTIP        # 1500
```

## 💡 모범 사례

### ✅ 좋은 예

```python
# 디자인 토큰 사용
from dashboard.design_system import DesignTokens as DT

color = DT.COLOR_PRIMARY
size = DT.FONT_SIZE_H1
spacing = DT.SPACE_4
```

### ❌ 나쁜 예

```python
# 하드코딩된 값 사용 (지양)
color = '#3B82F6'
size = 32
spacing = 16
```

### ✅ 테마별 색상

```python
# 테마에 따라 자동으로 색상 선택
from dashboard.design_system import Colors

dark_mode = st.session_state.get('dark_mode', False)
bg_color = Colors.get_bg_primary(dark_mode)
```

### ❌ 테마별 색상

```python
# 하드코딩으로 테마 분기 (지양)
if dark_mode:
    bg_color = '#111827'
else:
    bg_color = '#ffffff'
```

## 🔄 확장하기

### 새로운 색상 추가

`colors.py`에 추가:

```python
class Colors:
    # 새로운 색상 추가
    PURPLE_500 = '#8B5CF6'
    PURPLE_400 = '#A78BFA'
```

`tokens.py`에 재내보내기:

```python
class DesignTokens:
    COLOR_PURPLE = Colors.PURPLE_500
    COLOR_PURPLE_DARK = Colors.PURPLE_400
```

### 새로운 간격 값 추가

`spacing.py`에 추가:

```python
class Spacing:
    SPACE_24 = BASE_UNIT * 12  # 96px
```

## 📚 참고

- 색상 팔레트는 [Tailwind CSS](https://tailwindcss.com/docs/customizing-colors) 기반
- 간격은 8px 그리드 시스템 사용
- 모든 값은 픽셀(px) 단위

## 🎯 다음 단계

이 디자인 시스템을 사용하여:

1. **Atomic 컴포넌트 생성** (`components/atoms/`)
   - Button, Badge, Icon 등

2. **복합 컴포넌트 생성** (`components/molecules/`)
   - MetricCard, AlertBox, SearchBar 등

3. **복잡한 컴포넌트 생성** (`components/organisms/`)
   - DataTable, ChartGroup, NavigationBar 등

---

**마지막 업데이트**: 2025년 (Phase 3 완료)
