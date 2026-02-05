#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JavaScript 전체 페이지 분석 기반 PDF 버튼 탐지
- 모든 클릭 가능 요소를 검사
- PDF 관련 속성/텍스트를 가진 요소 찾기
"""

import logging
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


class JavaScriptDetector:
    """JavaScript로 전체 페이지 분석"""
    
    NAME = "javascript"
    PRIORITY = 7
    DESCRIPTION = "JavaScript로 전체 페이지 분석"
    
    def detect(self, driver):
        """
        PDF 버튼 탐지
        
        Args:
            driver: Selenium WebDriver
        
        Returns:
            WebElement 또는 None
        """
        try:
            script = """
                let results = [];
                document.querySelectorAll('a, button').forEach(el => {
                    let text = (el.innerText || '').toLowerCase();
                    let onclick = (el.getAttribute('onclick') || '').toLowerCase();
                    let classes = (el.className || '').toLowerCase();
                    let id = (el.id || '').toLowerCase();
                    
                    // PDF 관련 키워드 검색
                    if (text.includes('pdf') || 
                        onclick.includes('pdf') || 
                        onclick.includes('openpdf') ||
                        classes.includes('pdf') ||
                        id.includes('pdf') ||
                        el.querySelector('i.fa-file-pdf-o')) {
                        results.push(el);
                    }
                });
                return results.length > 0 ? results[0] : null;
            """
            
            button = driver.execute_script(script)
            
            if button:
                logger.debug(f"     ✓ javascript 탐지 성공")
                return button
            else:
                logger.debug(f"     ✗ javascript 탐지 실패")
                return None
        
        except Exception as e:
            logger.debug(f"     ✗ javascript 탐지 오류: {e}")
            return None
