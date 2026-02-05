#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Detectors 테스트 스크립트
- 각 전략을 개별적으로 테스트
- 어떤 전략이 성공하는지 확인
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from dotenv import load_dotenv
import logging

from modules.auth import login_to_krcon
from modules.pdf_detectors import (
    find_pdf_button,
    get_button_info,
    ButtonStrategy
)
from modules.pdf_detectors.strategies import STRATEGY_REGISTRY

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


def test_pdf_detectors():
    """모든 PDF 탐지 전략 테스트"""
    
    # Chrome 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 로그인
        logger.info("="*70)
        logger.info("🔐 로그인 중...")
        logger.info("="*70)
        
        if not login_to_krcon(driver):
            logger.error("❌ 로그인 실패")
            return
        
        logger.info("✅ 로그인 성공!")
        
        # 테스트할 페이지로 이동
        test_url = "https://krcon.krs.co.kr/Functions/TreeView/View.aspx?pn=11&mt=2&fc=1&fi=1"
        logger.info(f"\n📄 테스트 페이지로 이동...")
        logger.info(f"   URL: {test_url}")
        driver.get(test_url)
        
        import time
        time.sleep(3)
        
        # 각 전략 개별 테스트
        logger.info("\n" + "="*70)
        logger.info("🔍 각 전략 개별 테스트")
        logger.info("="*70)
        
        results = {}
        
        for strategy_name, detector in STRATEGY_REGISTRY.items():
            logger.info(f"\n📌 전략 '{strategy_name}' 테스트 중...")
            
            try:
                button = detector.detect(driver)
                
                if button:
                    info = get_button_info(button)
                    results[strategy_name] = {
                        'success': True,
                        'info': info
                    }
                    logger.info(f"   ✅ 성공!")
                    logger.info(f"      - ID: {info.get('id', 'N/A')}")
                    logger.info(f"      - Class: {info.get('class', 'N/A')}")
                else:
                    results[strategy_name] = {'success': False}
                    logger.info(f"   ❌ 실패")
                    
            except Exception as e:
                results[strategy_name] = {'success': False, 'error': str(e)}
                logger.error(f"   ❌ 오류: {e}")
        
        # 통합 테스트
        logger.info("\n" + "="*70)
        logger.info("🎯 통합 테스트 (자동 전략 선택)")
        logger.info("="*70)
        
        pdf_button = find_pdf_button(driver, log_attempts=True)
        
        if pdf_button:
            logger.info("\n✅ 통합 테스트 성공!")
            info = get_button_info(pdf_button)
            logger.info(f"   발견된 버튼 정보:")
            logger.info(f"   - ID: {info.get('id', 'N/A')}")
            logger.info(f"   - Class: {info.get('class', 'N/A')}")
            logger.info(f"   - onclick: {info.get('onclick', 'N/A')}")
            logger.info(f"   - Text: '{info.get('text', 'N/A')}'")
        else:
            logger.error("\n❌ 통합 테스트 실패!")
        
        # 결과 요약
        logger.info("\n" + "="*70)
        logger.info("📊 테스트 결과 요약")
        logger.info("="*70)
        
        success_count = sum(1 for r in results.values() if r.get('success'))
        fail_count = len(results) - success_count
        
        logger.info(f"\n총 {len(results)}개 전략 중:")
        logger.info(f"  ✅ 성공: {success_count}개")
        logger.info(f"  ❌ 실패: {fail_count}개")
        
        logger.info("\n성공한 전략:")
        for name, result in results.items():
            if result.get('success'):
                logger.info(f"  ✓ {name}")
        
        logger.info("\n실패한 전략:")
        for name, result in results.items():
            if not result.get('success'):
                error = result.get('error', '버튼 없음')
                logger.info(f"  ✗ {name} ({error})")
        
        # 권장 사항
        logger.info("\n" + "="*70)
        logger.info("💡 권장 전략")
        logger.info("="*70)
        
        if success_count > 0:
            successful_strategies = [name for name, r in results.items() if r.get('success')]
            logger.info(f"\n이 페이지에서는 다음 전략들을 사용하세요:")
            for strategy in successful_strategies[:3]:  # 상위 3개
                logger.info(f"  - {strategy}")
            
            logger.info(f"\n코드 예시:")
            logger.info(f'  pdf_button = find_pdf_button(driver, strategies={successful_strategies[:3]})')
        
        input("\n\n엔터를 누르면 종료합니다...")
        
    except Exception as e:
        logger.error(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        driver.quit()
        logger.info("\n✅ 테스트 완료")


if __name__ == "__main__":
    test_pdf_detectors()
