# KR-CON 자동 다운로더

KR-CON 사이트의 콘텐츠를 자동으로 수집하고 다운로드하는 도구

## 📁 프로젝트 구조

```
extract/
├── run.py                  # 🎯 메인 진입점
├── requirements.txt        # Python 패키지
├── README.md              # 📖 프로젝트 가이드
│
├── modules/               # 📦 핵심 모듈
│   ├── auth.py           # 로그인 관리
│   ├── tree_collector.py # 트리 구조 수집
│   ├── status.py         # 다운로드 상태 확인
│   └── pdf_detectors/    # 🆕 PDF 다운로드 모듈 (리팩토링 완료)
│       ├── __init__.py              # Public API (find_pdf_button, download_pdf)
│       ├── button_finder.py         # 버튼 찾기 (8가지 전략)
│       ├── detector_controller.py   # 다운로드 컨트롤러 (상황 분석 → 전략 선택)
│       ├── utils.py                 # 유틸리티
│       ├── README.md                # 📖 PDF 탐지 모듈 가이드
│       └── strategies/
│           ├── detector_cdp.py      # CDP로 Blob URL 다운로드
│           ├── detector_network.py  # requests로 직접 URL 다운로드
│           ├── detector_download.py # 다운로드 폴더 모니터링
│           └── button_strategies/   # 8개 버튼 검색 전략
│               ├── by_id.py
│               ├── by_fontawesome.py
│               ├── by_onclick.py
│               ├── by_btn_group.py
│               ├── by_text.py
│               ├── by_sibling.py
│               ├── by_javascript.py
│               └── by_css.py
│
├── tools/                 # 🔧 디버깅 & 테스트 도구
│   ├── inspect_page.py   # 페이지 구조 분석
│   ├── test_pdf_detectors.py        # PDF 탐지 전략 테스트
│   └── verify_new_architecture.py   # 리팩토링 검증 스크립트
│
├── docs/                  # 📚 문서
│   └── REFACTORING_COMPLETE_FINAL.md  # 리팩토링 완료 가이드
│
├── output/                # 📂 결과물
│   ├── downloads/        # 다운로드된 HTML/PDF
│   ├── tree_structure.json
│   └── download_progress.json
│
└── logs/                  # 📝 로그 파일
    ├── crawler.log
    ├── download.log
    └── failed_downloads.log
```

## 🆕 PDF Detectors 아키텍처 (2026.02.05 리팩토링 완료)

**버튼 찾기와 PDF 다운로드 로직을 분리한 새로운 아키텍처:**

```python
from modules.pdf_detectors import find_pdf_button, download_pdf

# 1단계: 버튼 찾기 (8가지 전략 자동 시도)
button = find_pdf_button(driver)

# 2단계: PDF 다운로드 (상황 분석 후 최적 전략 자동 선택)
path = download_pdf(driver, button, "/output", "file.pdf")
```

**다운로드 전략 (자동 선택):**
- `detector_cdp`: Blob URL → CDP `Page.printToPDF`
- `detector_network`: 직접 PDF URL → `requests.get()`
- `detector_download`: 브라우저 다운로드 폴더 모니터링

📖 **상세 가이드**: `docs/REFACTORING_COMPLETE_FINAL.md`

## 🚀 사용 방법

### 1️⃣ 환경 설정

```bash
# 가상 환경 활성화
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 패키지 설치
pip install -r requirements.txt
```

### 2️⃣ 로그인 정보 설정

`.env` 파일 생성:
```env
KRCON_USER_ID=your_id
KRCON_PASSWORD=your_password
```

### 3️⃣ 실행

```bash
python run.py
```

**자동으로 수행되는 작업:**
1. ✅ 로그인
2. ✅ 트리 구조 수집 (없을 경우)
3. ✅ 진행 상황 확인
4. ✅ 콘텐츠 다운로드 (HTML + PDF)
5. ✅ Ctrl+C 안전 종료

## 🔧 개별 도구 사용

### 트리 구조만 수집
```bash
cd modules
python -m tree_collector
```

### 다운로드 상태 확인
```bash
cd modules
python -m status
```

### 페이지 구조 분석 (디버깅)
```bash
cd tools
python inspect_page.py
```

### 🆕 PDF 탐지 전략 테스트
```bash
cd tools
python test_pdf_detectors.py
```

이 도구는 8가지 PDF 버튼 탐지 전략을 개별적으로 테스트하고,
어떤 전략이 성공하는지 확인할 수 있습니다.

상세 가이드: [`modules/PDF_DETECTORS_README.md`](modules/PDF_DETECTORS_README.md)

## ⚙️ 설정

`run.py` 파일에서 수정 가능:

```python
# Rate limiting
MAX_REQUESTS_PER_MINUTE = 10  # 분당 최대 요청 수
DELAY_RANGE = (3, 7)           # 요청 간 지연 시간 (초)
MAX_RETRIES = 3                # 재시도 횟수
PAGE_LOAD_TIMEOUT = 30         # 페이지 로드 타임아웃 (초)
```

## 📊 특징

- ✅ **단일 진입점**: `run.py` 하나로 모든 작업 자동화
- ✅ **자동 재개**: 중단된 지점부터 이어서 다운로드
- ✅ **Rate Limiting**: 서버 부하 방지
- ✅ **안전 종료**: Ctrl+C로 언제든 안전하게 중단
- ✅ **모듈화**: 각 기능별로 독립 모듈 분리
- ✅ **로그 관리**: 모든 작업 로그 자동 기록

## 🐛 문제 해결

### 로그인 실패
- `.env` 파일의 로그인 정보 확인
- VPN 연결 상태 확인

### 다운로드 중단
- `output/download_progress.json` 확인
- `run.py` 재실행시 자동으로 이어서 진행

### PDF 다운로드 안됨
- `tools/inspect_page.py` 실행하여 페이지 구조 분석
- `logs/download.log` 확인

## 📝 로그 확인

```bash
# 전체 로그
cat logs/download.log

# 실패한 다운로드만
cat logs/failed_downloads.log

# 트리 수집 로그
cat logs/crawler.log
```

## 🔄 업데이트 이력

### v2.0.0 (2026-02-04)
- 모듈식 구조로 전면 개편
- 단일 진입점 (`run.py`) 구현
- 결과물/로그 폴더 분리
- 자동 트리 수집 기능 추가

### v1.0.0 (2026-02-03)
- 초기 버전
- 기본 다운로드 기능 구현
