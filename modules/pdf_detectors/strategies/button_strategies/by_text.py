#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
텍스트 내용 기반 PDF 버튼 탐지
- "PDF" 텍스트를 포함한 링크/버튼 찾기
- 대소문자 무시
"""

import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)


class TextDetector:
    """텍스트 내용으로 PDF 버튼 찾기"""
    
    NAME = "text"
    PRIORITY = 5
    DESCRIPTION = '"PDF" 텍스트를 포함한 요소 찾기'
    
    def detect(self, driver):
        """
        PDF 버튼 탐지
        
        Args:
            driver: Selenium WebDriver
        
        Returns:
            WebElement 또는 None
        """
        try:
            button = driver.find_element(By.XPATH, 
                "//a[contains(translate(., 'pdf', 'PDF'), 'PDF') or contains(translate(., 'Pdf', 'PDF'), 'PDF')]")
            logger.debug(f"     ✓ text 탐지 성공")
            return button
        except NoSuchElementException:
            logger.debug(f"     ✗ text 탐지 실패")
            return None
        except Exception as e:
            logger.debug(f"     ✗ text 탐지 오류: {e}")
            return None
