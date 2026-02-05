# PDF Detectors 모듈 사용 가이드

## 📋 개요

PDF 다운로드 버튼을 찾기 위한 **8가지 독립적인 탐지 전략**을 제공합니다.  
각 전략은 독립적으로 작동하며, 필요에 따라 선택적으로 사용할 수 있습니다.

---

## 🎯 탐지 전략 목록

### 1. `pdf_detector_by_id`
- **방법**: ID 속성으로 찾기 (`#ankPrint`)
- **장점**: 가장 빠르고 정확
- **단점**: ID가 변경되면 실패
- **우선순위**: ⭐⭐⭐⭐⭐

### 2. `pdf_detector_by_fontawesome_icon`
- **방법**: FontAwesome 아이콘 클래스로 찾기 (`.fa-file-pdf-o`)
- **장점**: 아이콘이 변경되지 않으면 안정적
- **단점**: 아이콘 라이브러리 변경 시 실패
- **우선순위**: ⭐⭐⭐⭐

### 3. `pdf_detector_by_onclick_attribute`
- **방법**: onclick 속성에서 함수명 검색 (`openPdf()`)
- **장점**: JavaScript 함수명 기반으로 안정적
- **단점**: 함수명 변경 시 실패
- **우선순위**: ⭐⭐⭐⭐

### 4. `pdf_detector_by_btn_group`
- **방법**: `.btn-group` 내부의 PDF 아이콘 검색
- **장점**: 버튼 그룹 구조가 유지되면 안정적
- **단점**: 레이아웃 변경 시 실패
- **우선순위**: ⭐⭐⭐

### 5. `pdf_detector_by_text_content`
- **방법**: "PDF" 텍스트를 포함한 요소 찾기
- **장점**: 가장 범용적
- **단점**: 오탐 가능성 (다른 PDF 링크)
- **우선순위**: ⭐⭐

### 6. `pdf_detector_by_memo_sibling`
- **방법**: MEMO 버튼의 형제 요소로 찾기
- **장점**: 버튼 순서가 유지되면 안정적
- **단점**: 레이아웃 변경에 취약
- **우선순위**: ⭐⭐⭐

### 7. `pdf_detector_by_javascript_analysis`
- **방법**: JavaScript로 전체 페이지 분석
- **장점**: 가장 포괄적
- **단점**: 성능 저하 가능
- **우선순위**: ⭐⭐

### 8. `pdf_detector_by_css_selector`
- **방법**: 복합 CSS 선택자 사용
- **장점**: 여러 패턴 동시 시도
- **단점**: CSS 구조 변경 시 실패
- **우선순위**: ⭐⭐⭐

---

## 💻 사용법

### 기본 사용 (모든 전략 자동 시도)

```python
from modules.pdf_detectors import find_pdf_button, get_button_info

# 모든 전략을 순서대로 시도
pdf_button = find_pdf_button(driver)

if pdf_button:
    print("PDF 버튼 발견!")
    info = get_button_info(pdf_button)
    print(f"ID: {info['id']}")
    print(f"onclick: {info['onclick']}")
else:
    print("PDF 버튼 없음")
```

### 특정 전략만 사용

```python
# 빠른 전략만 사용 (ID, FontAwesome, onclick)
pdf_button = find_pdf_button(driver, strategies=["ID", "FontAwesome", "onclick"])

# 안정적인 전략만 사용
pdf_button = find_pdf_button(driver, strategies=["onclick", "btn-group", "css"])

# JavaScript 분석만 사용
pdf_button = find_pdf_button(driver, strategies=["javascript"])
```

### 로그 비활성화

```python
# 로그 없이 조용하게 실행
pdf_button = find_pdf_button(driver, log_attempts=False)
```

### 개별 전략 직접 호출

```python
from modules.pdf_detectors import (
    pdf_detector_by_id,
    pdf_detector_by_fontawesome_icon,
    pdf_detector_by_onclick_attribute
)

# ID로만 찾기
button = pdf_detector_by_id(driver)

# FontAwesome으로만 찾기
button = pdf_detector_by_fontawesome_icon(driver)
```

---

## 🔧 커스터마이징

### 새로운 전략 추가하기

1. **새로운 함수 작성**

```python
def pdf_detector_by_custom_method(driver):
    """
    커스텀 탐지 방법
    - 당신만의 방법으로 PDF 버튼 찾기
    """
    try:
        button = driver.find_element(By.YOUR_METHOD, "YOUR_SELECTOR")
        logger.info(f"     ✓ 커스텀 방법 성공!")
        return button
    except NoSuchElementException:
        logger.debug(f"     ✗ 커스텀 방법 실패")
        return None
```

2. **레지스트리에 등록**

```python
PDF_DETECTORS = [
    ("ID", pdf_detector_by_id),
    ("FontAwesome", pdf_detector_by_fontawesome_icon),
    # ... 기존 전략들 ...
    ("custom", pdf_detector_by_custom_method),  # 추가!
]
```

3. **사용하기**

```python
pdf_button = find_pdf_button(driver, strategies=["custom"])
```

---

## 🎯 권장 사용 시나리오

### 시나리오 1: 빠른 처리 우선
```python
# 빠른 전략 3개만 사용
strategies = ["ID", "FontAwesome", "onclick"]
pdf_button = find_pdf_button(driver, strategies=strategies)
```

### 시나리오 2: 안정성 우선
```python
# 구조 기반 전략 사용
strategies = ["onclick", "btn-group", "sibling", "css"]
pdf_button = find_pdf_button(driver, strategies=strategies)
```

### 시나리오 3: 포괄적 검색
```python
# 모든 전략 사용 (기본값)
pdf_button = find_pdf_button(driver)
```

### 시나리오 4: 디버깅
```python
# JavaScript 분석으로 모든 PDF 관련 요소 찾기
strategies = ["javascript"]
pdf_button = find_pdf_button(driver, strategies=strategies, log_attempts=True)
```

---

## 📊 성능 비교

| 전략 | 속도 | 안정성 | 정확도 |
|------|------|--------|--------|
| ID | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| FontAwesome | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| onclick | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| btn-group | ⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| text | ⚡⚡⚡ | ⭐⭐ | ⭐⭐⭐ |
| sibling | ⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| javascript | ⚡⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| css | ⚡⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 🐛 디버깅 팁

### 로그 확인하기

```python
# 상세 로그 활성화
import logging
logging.basicConfig(level=logging.DEBUG)

# PDF 버튼 찾기 (모든 시도 과정 출력)
pdf_button = find_pdf_button(driver, log_attempts=True)
```

### 버튼 정보 상세 확인

```python
from modules.pdf_detectors import get_button_info

button = find_pdf_button(driver)
if button:
    info = get_button_info(button)
    print(json.dumps(info, indent=2, ensure_ascii=False))
```

출력 예시:
```json
{
  "tag": "a",
  "id": "ankPrint",
  "class": "btn btn-default",
  "onclick": "openPdf()",
  "text": "",
  "href": "javascript:void(0);"
}
```

---

## 🔄 전략 우선순위 변경

기본 순서를 변경하고 싶다면 `pdf_detectors.py`에서 `PDF_DETECTORS` 리스트 순서를 변경하세요:

```python
# modules/pdf_detectors.py

PDF_DETECTORS = [
    ("onclick", pdf_detector_by_onclick_attribute),      # 1순위
    ("ID", pdf_detector_by_id),                          # 2순위
    ("FontAwesome", pdf_detector_by_fontawesome_icon),   # 3순위
    # ... 나머지 ...
]
```

---

## 📝 예제 코드

### 완전한 사용 예제

```python
from selenium import webdriver
from modules.pdf_detectors import find_pdf_button, get_button_info

# WebDriver 초기화
driver = webdriver.Chrome()
driver.get("https://krcon.krs.co.kr/...")

# PDF 버튼 찾기
pdf_button = find_pdf_button(driver)

if pdf_button:
    # 버튼 정보 확인
    info = get_button_info(pdf_button)
    print(f"✅ PDF 버튼 발견!")
    print(f"   ID: {info['id']}")
    print(f"   onclick: {info['onclick']}")
    
    # 버튼 클릭
    pdf_button.click()
    
else:
    print("❌ PDF 버튼을 찾을 수 없습니다")
```

---

## 🎓 모듈 구조

```
modules/pdf_detectors.py
├── pdf_detector_by_id()                  # 전략 1
├── pdf_detector_by_fontawesome_icon()    # 전략 2
├── pdf_detector_by_onclick_attribute()   # 전략 3
├── pdf_detector_by_btn_group()           # 전략 4
├── pdf_detector_by_text_content()        # 전략 5
├── pdf_detector_by_memo_sibling()        # 전략 6
├── pdf_detector_by_javascript_analysis() # 전략 7
├── pdf_detector_by_css_selector()        # 전략 8
├── PDF_DETECTORS                         # 전략 레지스트리
├── find_pdf_button()                     # 메인 함수
└── get_button_info()                     # 유틸리티
```

---

## 🚀 현재 `run.py`에서의 사용

```python
from modules.pdf_detectors import find_pdf_button, get_button_info

def download_pdf_files(driver, node, folder_path):
    # PDF 버튼 찾기 (모든 전략 자동 시도)
    pdf_button = find_pdf_button(driver, log_attempts=True)
    
    if not pdf_button:
        logger.info(f"  ℹ️  PDF 버튼 없음")
        return 0
    
    # 버튼 정보 로깅
    button_info = get_button_info(pdf_button)
    logger.info(f"  ✅ PDF 버튼 발견!")
    logger.info(f"     - ID: {button_info.get('id', 'N/A')}")
    logger.info(f"     - onclick: {button_info.get('onclick', 'N/A')}")
    
    # 버튼 클릭 및 PDF 다운로드
    pdf_button.click()
    # ...
```

---

## 📌 주의사항

1. **순서가 중요**: 빠른 전략부터 시도하므로 `PDF_DETECTORS` 순서를 고려하세요
2. **로그 레벨**: `DEBUG` 레벨에서는 모든 실패도 기록됩니다
3. **성능**: JavaScript 분석은 느리므로 마지막 수단으로 사용하세요
4. **예외 처리**: 각 전략은 독립적으로 실패해도 다음 전략을 시도합니다

---

**작성일**: 2026-02-05  
**버전**: 1.0.0
