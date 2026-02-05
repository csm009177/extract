#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ID 기반 PDF 버튼 탐지
- 가장 빠르고 정확한 방법
- ID가 변경되면 실패
"""

import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)


class IDDetector:
    """ID 속성으로 PDF 버튼 찾기 (#ankPrint)"""
    
    NAME = "ID"
    PRIORITY = 1  # 우선순위 (낮을수록 먼저 실행)
    DESCRIPTION = "ID 속성으로 찾기 (#ankPrint)"
    
    def detect(self, driver):
        """
        PDF 버튼 탐지
        
        Args:
            driver: Selenium WebDriver
        
        Returns:
            WebElement 또는 None
        """
        try:
            button = driver.find_element(By.ID, "ankPrint")
            logger.debug(f"     ✓ ID 탐지 성공: #ankPrint")
            return button
        except NoSuchElementException:
            logger.debug(f"     ✗ ID 탐지 실패")
            return None
        except Exception as e:
            logger.debug(f"     ✗ ID 탐지 오류: {e}")
            return None
