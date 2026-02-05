#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
btn-group 내부 검색 기반 PDF 버튼 탐지
- .btn-group 클래스 내의 PDF 아이콘 찾기
- 버튼 그룹 구조 활용
"""

import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)


class BtnGroupDetector:
    """btn-group 내부에서 PDF 버튼 찾기"""
    
    NAME = "btn-group"
    PRIORITY = 4
    DESCRIPTION = ".btn-group 내부의 PDF 아이콘 검색"
    
    def detect(self, driver):
        """
        PDF 버튼 탐지
        
        Args:
            driver: Selenium WebDriver
        
        Returns:
            WebElement 또는 None
        """
        try:
            btn_group = driver.find_element(By.CLASS_NAME, "btn-group")
            buttons = btn_group.find_elements(By.TAG_NAME, "a")
            
            for btn in buttons:
                # PDF 아이콘이 있는 버튼 찾기
                icons = btn.find_elements(By.CSS_SELECTOR, "i.fa-file-pdf-o")
                if icons:
                    logger.debug(f"     ✓ btn-group 탐지 성공")
                    return btn
            
            logger.debug(f"     ✗ btn-group 탐지 실패: PDF 버튼 없음")
            return None
        except NoSuchElementException:
            logger.debug(f"     ✗ btn-group 탐지 실패")
            return None
        except Exception as e:
            logger.debug(f"     ✗ btn-group 탐지 오류: {e}")
            return None
