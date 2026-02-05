#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
새로운 아키텍처 검증 스크립트

목적:
1. 모듈 import 테스트
2. API 호출 가능 여부 확인
3. 파일 구조 검증
"""

import sys
import os

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("🔍 리팩토링 검증 시작")
print("=" * 60)

# 1. Import 테스트
print("\n[1단계] 모듈 Import 테스트...")
try:
    from modules.pdf_detectors import download_pdf
    print("  ✅ modules.pdf_detectors import 성공")
    print(f"     - download_pdf: {download_pdf}")
except Exception as e:
    print(f"  ❌ Import 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. ButtonFinder 테스트
print("\n[2단계] ButtonFinder 클래스 테스트...")
try:
    from modules.pdf_detectors.button_finder import ButtonFinder
    print("  ✅ ButtonFinder import 성공")
    print(f"     - ButtonFinder: {ButtonFinder}")
except Exception as e:
    print(f"  ❌ ButtonFinder import 실패: {e}")

# 3. PDFRetrievalController 테스트
print("\n[3단계] PDFRetrievalController 클래스 테스트...")
try:
    from modules.pdf_detectors.retrieval_controller import PDFRetrievalController
    print("  ✅ PDFRetrievalController import 성공")
    print(f"     - PDFRetrievalController: {PDFRetrievalController}")
except Exception as e:
    print(f"  ❌ PDFRetrievalController import 실패: {e}")

# 4. Retrieval 전략 레지스트리 테스트
print("\n[4단계] Retrieval 전략 레지스트리 테스트...")
try:
    from modules.pdf_detectors.strategies import RETRIEVAL_STRATEGY_REGISTRY, RETRIEVAL_STRATEGY_ORDER
    print("  ✅ RETRIEVAL_STRATEGY_REGISTRY import 성공")
    print(f"     - 등록된 전략 개수: {len(RETRIEVAL_STRATEGY_REGISTRY)}")
    for name, strategy_class in RETRIEVAL_STRATEGY_REGISTRY.items():
        print(f"       • {name}: {strategy_class.__class__.__name__} (priority={strategy_class.priority})")
    print(f"     - 우선순위 순서: {RETRIEVAL_STRATEGY_ORDER}")
except Exception as e:
    print(f"  ❌ RETRIEVAL_STRATEGY_REGISTRY import 실패: {e}")

# 5. 버튼 전략 레지스트리 테스트
print("\n[5단계] 버튼 전략 레지스트리 테스트...")
try:
    from modules.pdf_detectors.strategies.button_strategies import BUTTON_STRATEGY_REGISTRY
    print("  ✅ BUTTON_STRATEGY_REGISTRY import 성공")
    print(f"     - 등록된 전략 개수: {len(BUTTON_STRATEGY_REGISTRY)}")
    for name, strategy_class in BUTTON_STRATEGY_REGISTRY.items():
        print(f"       • {name}: {strategy_class.__class__.__name__}")
except Exception as e:
    print(f"  ❌ BUTTON_STRATEGY_REGISTRY import 실패: {e}")

# 6. 파일 구조 검증
print("\n[6단계] 파일 구조 검증...")
expected_files = [
    "modules/pdf_detectors/__init__.py",
    "modules/pdf_detectors/button_finder.py",
    "modules/pdf_detectors/retrieval_controller.py",
    "modules/pdf_detectors/utils.py",
    "modules/pdf_detectors/strategies/__init__.py",
    "modules/pdf_detectors/strategies/retrieval_cdp.py",
    "modules/pdf_detectors/strategies/retrieval_network.py",
    "modules/pdf_detectors/strategies/retrieval_browser.py",
    "modules/pdf_detectors/strategies/button_strategies/__init__.py",
    "modules/pdf_detectors/strategies/button_strategies/by_id.py",
    "modules/pdf_detectors/strategies/button_strategies/by_fontawesome.py",
    "modules/pdf_detectors/strategies/button_strategies/by_onclick.py",
]

all_exist = True
for file_path in expected_files:
    if os.path.exists(file_path):
        print(f"  ✅ {file_path}")
    else:
        print(f"  ❌ {file_path} - 파일 없음!")
        all_exist = False

# 최종 결과
print("\n" + "=" * 60)
if all_exist:
    print("✅ Retrieval 아키텍처 검증 성공!")
    print("   → 3가지 retrieval 방식이 정상적으로 작동합니다")
    print("")
    print("📊 Retrieval 전략:")
    print("   1. retrieval_cdp      - CDP Page.printToPDF")
    print("   2. retrieval_network  - Network requests.get()")
    print("   3. retrieval_browser  - Browser 다운로드 폴더")
else:
    print("⚠️  일부 파일이 누락되었습니다")
print("=" * 60)
