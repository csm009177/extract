#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF 버튼 찾기 로직
- 다양한 전략으로 PDF 버튼 탐지
"""

import logging
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from .strategies.button_strategies import BUTTON_STRATEGY_REGISTRY, BUTTON_STRATEGY_ORDER

logger = logging.getLogger(__name__)


class ButtonFinder:
    """PDF 버튼 찾기"""
    
    # 사전 정의된 전략 조합
    PRESET_STRATEGIES = {
        "fast": ["id", "fontawesome", "onclick"],
        "stable": ["onclick", "btn_group", "sibling", "css"],
        "fallback": ["javascript"],
        "auto": None  # None이면 모든 전략 사용
    }
    
    def __init__(self, driver, log_attempts=True):
        self.driver = driver
        self.log_attempts = log_attempts
        
        if log_attempts:
            logger.info(f"  🔍 Button Finder 초기화")
            logger.info(f"     - 등록된 전략: {len(BUTTON_STRATEGY_REGISTRY)}개")
    
    def find(self, strategy="auto", wait_for_page=True, max_wait=10):
        """
        PDF 버튼 찾기
        
        Args:
            strategy: str - 전략 이름 또는 프리셋
            wait_for_page: bool - 페이지 로딩 대기 여부
            max_wait: int - 최대 대기 시간 (초)
        
        Returns:
            WebElement 또는 None
        """
        # 1. 페이지 로딩 대기 (타이밍 이슈 대비)
        if wait_for_page:
            try:
                WebDriverWait(self.driver, max_wait).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                time.sleep(1)  # 추가 안전 대기
                if self.log_attempts:
                    logger.info(f"  ⏳ 페이지 로딩 완료")
            except Exception as e:
                if self.log_attempts:
                    logger.warning(f"  ⚠️  페이지 로딩 대기 실패: {e}")
        
        strategy = str(strategy).lower()
        
        # 2. 팝업/경고창 처리 (팝업 이슈 대비)
        self._close_popups()
        
        # 전략 리스트 결정
        if strategy == "auto" or strategy not in self.PRESET_STRATEGIES:
            strategies = BUTTON_STRATEGY_ORDER
        elif strategy in self.PRESET_STRATEGIES:
            preset = self.PRESET_STRATEGIES[strategy]
            strategies = preset if preset else BUTTON_STRATEGY_ORDER
        else:
            strategies = [strategy]
        
        # 전략 실행
        if self.log_attempts:
            logger.info(f"  📌 PDF 버튼 탐지 시작")
        
        for idx, strategy_name in enumerate(strategies, 1):
            if self.log_attempts:
                logger.info(f"     [{idx}/{len(strategies)}] {strategy_name} 시도...")
            
            try:
                detector = BUTTON_STRATEGY_REGISTRY.get(strategy_name)
                if not detector:
                    logger.warning(f"     ⚠️  알 수 없는 전략: {strategy_name}")
                    continue
                
                button = detector.detect(self.driver)
                
                if button:
                    if self.log_attempts:
                        logger.info(f"     ✅ 버튼 발견!")
                        logger.info(f"        [전략] {strategy_name} ({detector.NAME})")
                        logger.info(f"        [우선순위] {detector.PRIORITY}")
                        
                        # 버튼 정보 출력
                        from .utils import get_button_info
                        info = get_button_info(button)
                        if info:
                            if info.get('id'):
                                logger.info(f"        [ID] {info.get('id')}")
                            if info.get('class'):
                                logger.info(f"        [Class] {info.get('class')}")
                            if info.get('onclick'):
                                logger.info(f"        [onclick] {info.get('onclick')}")
                    
                    return button
            
            except Exception as e:
                logger.error(f"     ❌ 오류 ({strategy_name}): {e}")
        
        if self.log_attempts:
            logger.warning(f"  ⚠️  PDF 버튼을 찾을 수 없습니다")
        
        return None
    
    def _close_popups(self):
        """팝업/경고창 자동 닫기 (팝업 이슈 대비)"""
        try:
            # Alert 처리
            alert = self.driver.switch_to.alert
            alert.accept()
            if self.log_attempts:
                logger.info(f"  ✅ Alert 창 닫음")
        except:
            pass  # Alert 없으면 무시
        
        try:
            # 일반 팝업 처리 (새 창)
            windows = self.driver.window_handles
            if len(windows) > 1:
                # 원본 창 저장
                original = windows[0]
                # 팝업 닫기
                for window in windows[1:]:
                    self.driver.switch_to.window(window)
                    self.driver.close()
                    if self.log_attempts:
                        logger.info(f"  ✅ 팝업 창 닫음")
                # 원본 창으로 복귀
                self.driver.switch_to.window(original)
        except:
            pass  # 오류 무시
