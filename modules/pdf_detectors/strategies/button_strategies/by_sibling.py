#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMO 버튼 형제 요소 기반 PDF 버튼 탐지
- #ankMemo 버튼을 먼저 찾고
- 그 옆의 형제 요소 중 PDF 버튼 찾기
"""

import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)


class SiblingDetector:
    """MEMO 버튼의 형제 요소로 PDF 버튼 찾기"""
    
    NAME = "sibling"
    PRIORITY = 6
    DESCRIPTION = "MEMO 버튼의 형제 요소로 찾기"
    
    def detect(self, driver):
        """
        PDF 버튼 탐지
        
        Args:
            driver: Selenium WebDriver
        
        Returns:
            WebElement 또는 None
        """
        try:
            memo_button = driver.find_element(By.ID, "ankMemo")
            # preceding-sibling: MEMO 이전의 형제 요소 중 PDF 버튼
            pdf_button = memo_button.find_element(By.XPATH, 
                "preceding-sibling::a[@id='ankPrint' or contains(@onclick, 'openPdf')]")
            logger.debug(f"     ✓ sibling 탐지 성공")
            return pdf_button
        except NoSuchElementException:
            logger.debug(f"     ✗ sibling 탐지 실패")
            return None
        except Exception as e:
            logger.debug(f"     ✗ sibling 탐지 오류: {e}")
            return None
