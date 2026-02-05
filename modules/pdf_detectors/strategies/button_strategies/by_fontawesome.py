#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FontAwesome 아이콘 기반 PDF 버튼 탐지
- fa-file-pdf-o 클래스를 가진 아이콘 찾기
- 아이콘의 부모 <a> 태그가 버튼
"""

import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)


class FontAwesomeDetector:
    """FontAwesome 아이콘으로 PDF 버튼 찾기"""
    
    NAME = "FontAwesome"
    PRIORITY = 2
    DESCRIPTION = "FontAwesome 아이콘 클래스로 찾기 (.fa-file-pdf-o)"
    
    def detect(self, driver):
        """
        PDF 버튼 탐지
        
        Args:
            driver: Selenium WebDriver
        
        Returns:
            WebElement 또는 None
        """
        try:
            # fa-file-pdf-o 아이콘 찾기
            icon = driver.find_element(By.CSS_SELECTOR, "i.fa.fa-file-pdf-o")
            # 부모 <a> 태그 찾기
            button = icon.find_element(By.XPATH, "..")
            logger.debug(f"     ✓ FontAwesome 탐지 성공")
            return button
        except NoSuchElementException:
            logger.debug(f"     ✗ FontAwesome 탐지 실패")
            return None
        except Exception as e:
            logger.debug(f"     ✗ FontAwesome 탐지 오류: {e}")
            return None
