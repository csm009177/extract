#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Detectors 공통 유틸리티
"""

import logging

logger = logging.getLogger(__name__)


def get_button_info(button):
    """
    버튼 정보 추출
    
    Args:
        button: Selenium WebElement
    
    Returns:
        dict: 버튼 속성 정보 또는 None
    """
    if not button:
        return None
    
    try:
        info = {
            "tag": button.tag_name,
            "id": button.get_attribute("id") or "",
            "class": button.get_attribute("class") or "",
            "onclick": button.get_attribute("onclick") or "",
            "href": button.get_attribute("href") or "",
            "text": button.text or "",
        }
        return info
    except Exception as e:
        logger.error(f"버튼 정보 추출 실패: {e}")
        return None


def validate_button(button):
    """
    PDF 버튼인지 검증
    
    Args:
        button: Selenium WebElement
    
    Returns:
        bool: PDF 버튼이면 True
    """
    if not button:
        return False
    
    info = get_button_info(button)
    if not info:
        return False
    
    # PDF 관련 키워드 체크
    keywords = ["pdf", "openpdf", "ankprint", "fa-file-pdf"]
    
    for key, value in info.items():
        value_lower = str(value).lower()
        if any(keyword in value_lower for keyword in keywords):
            return True
    
    return False
