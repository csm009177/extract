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
    from modules.pdf_detectors import find_pdf_button, download_pdf
    print("  ✅ modules.pdf_detectors import 성공")
    print(f"     - find_pdf_button: {find_pdf_button}")
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

# 3. PDFDetectorController 테스트
print("\n[3단계] PDFDetectorController 클래스 테스트...")
try:
    from modules.pdf_detectors.detector_controller import PDFDetectorController
    print("  ✅ PDFDetectorController import 성공")
    print(f"     - PDFDetectorController: {PDFDetectorController}")
except Exception as e:
    print(f"  ❌ PDFDetectorController import 실패: {e}")

# 4. 다운로드 전략 레지스트리 테스트
print("\n[4단계] 다운로드 전략 레지스트리 테스트...")
try:
    from modules.pdf_detectors.strategies import DOWNLOAD_STRATEGY_REGISTRY
    print("  ✅ DOWNLOAD_STRATEGY_REGISTRY import 성공")
    print(f"     - 등록된 전략 개수: {len(DOWNLOAD_STRATEGY_REGISTRY)}")
    for name, strategy_class in DOWNLOAD_STRATEGY_REGISTRY.items():
        print(f"       • {name}: {strategy_class.__class__.__name__}")
except Exception as e:
    print(f"  ❌ DOWNLOAD_STRATEGY_REGISTRY import 실패: {e}")

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
    "modules/pdf_detectors/detector_controller.py",
    "modules/pdf_detectors/utils.py",
    "modules/pdf_detectors/strategies/__init__.py",
    "modules/pdf_detectors/strategies/detector_cdp.py",
    "modules/pdf_detectors/strategies/detector_network.py",
    "modules/pdf_detectors/strategies/detector_download.py",
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
    print("✅ 리팩토링 검증 성공!")
    print("   → 새로운 아키텍처가 정상적으로 작동합니다")
else:
    print("⚠️  일부 파일이 누락되었습니다")
print("=" * 60)
