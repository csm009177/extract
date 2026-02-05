#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSS Selector 조합 기반 PDF 버튼 탐지
- 복합 CSS 선택자로 정확하게 찾기
- 여러 CSS 패턴 시도
"""

import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)


class CSSDetector:
    """CSS Selector 조합으로 PDF 버튼 찾기"""
    
    NAME = "css"
    PRIORITY = 8
    DESCRIPTION = "복합 CSS 선택자 사용"
    
    CSS_SELECTORS = [
        "a#ankPrint",
        "a[onclick*='openPdf']",
        "a i.fa-file-pdf-o",
        ".btn-group a i.fa-file-pdf-o",
        "a.btn i.fa-file-pdf-o",
    ]
    
    def detect(self, driver):
        """
        PDF 버튼 탐지
        
        Args:
            driver: Selenium WebDriver
        
        Returns:
            WebElement 또는 None
        """
        for selector in self.CSS_SELECTORS:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                
                # 아이콘이면 부모 <a> 찾기
                if element.tag_name == 'i':
                    button = element.find_element(By.XPATH, "..")
                else:
                    button = element
                
                logger.debug(f"     ✓ css 탐지 성공: {selector}")
                return button
            
            except NoSuchElementException:
                continue
            except Exception as e:
                logger.debug(f"     CSS selector '{selector}' 오류: {e}")
                continue
        
        logger.debug(f"     ✗ css 탐지 실패")
        return None
