#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
onclick 속성 기반 PDF 버튼 탐지
- onclick="openPdf()" 함수를 가진 요소 찾기
- JavaScript 함수명 기반 탐지
"""

import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)


class OnClickDetector:
    """onclick 속성으로 PDF 버튼 찾기"""
    
    NAME = "onclick"
    PRIORITY = 3
    DESCRIPTION = "onclick 속성에서 함수명 검색 (openPdf)"
    
    def detect(self, driver):
        """
        PDF 버튼 탐지
        
        Args:
            driver: Selenium WebDriver
        
        Returns:
            WebElement 또는 None
        """
        try:
            button = driver.find_element(By.XPATH, "//a[contains(@onclick, 'openPdf')]")
            logger.debug(f"     ✓ onclick 탐지 성공")
            return button
        except NoSuchElementException:
            logger.debug(f"     ✗ onclick 탐지 실패")
            return None
        except Exception as e:
            logger.debug(f"     ✗ onclick 탐지 오류: {e}")
            return None
