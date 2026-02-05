#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Detectors 모듈 - 진입점
- find_pdf_button: PDF 버튼 찾기 (8가지 버튼 전략 사용)
- download_pdf: PDF 다운로드 (3가지 다운로드 전략 자동 선택)

Usage:
    from modules.pdf_detectors import find_pdf_button, download_pdf
    
    # 1단계: 버튼 찾기
    button = find_pdf_button(driver)
    
    # 2단계: PDF 다운로드
    path = download_pdf(driver, button, "/output", "test.pdf")
"""

from .button_finder import ButtonFinder
from .detector_controller import PDFDetectorController
from .utils import get_button_info, validate_button


def find_pdf_button(driver, strategy="auto", log_attempts=True):
    """
    PDF 버튼 찾기 (8가지 버튼 전략 사용)
    
    Args:
        driver: Selenium WebDriver
        strategy: str - 전략 이름
                  - "auto" (기본): 8가지 전략 순차 시도
                  - "fast": 빠른 전략만 (id, fontawesome, onclick)
                  - "stable": 안정적인 전략 (onclick, btn_group, sibling, css)
                  - "id", "fontawesome" 등: 특정 전략만 사용
        log_attempts: bool - 시도 과정 로그 출력 여부
    
    Returns:
        WebElement: 찾은 PDF 버튼
        None: 버튼을 찾지 못함
    
    Examples:
        >>> # 기본 사용
        >>> button = find_pdf_button(driver)
        
        >>> # 빠른 모드
        >>> button = find_pdf_button(driver, strategy="fast")
        
        >>> # 특정 전략
        >>> button = find_pdf_button(driver, strategy="id")
    """
    finder = ButtonFinder(driver, log_attempts)
    return finder.find(strategy)


def download_pdf(driver, button, folder_path, filename, node_name="Unknown", log_attempts=True):
    """
    PDF 다운로드 (상황 분석 → 자동 전략 선택)
    
    Controller가 상황을 분석:
        - 새 창 열림? Blob URL? PDF URL?
        → detector_cdp (CDP Page.printToPDF)
        → detector_network (requests.get)
        → detector_download (다운로드 폴더 모니터링)
    
    Args:
        driver: Selenium WebDriver
        button: WebElement - PDF 버튼
        folder_path: str - 저장 폴더 경로
        filename: str - 파일명 (예: "example.pdf")
        node_name: str - 노드 이름 (로그용)
        log_attempts: bool - 시도 과정 로그 출력 여부
    
    Returns:
        str: 저장된 파일 경로
        None: 다운로드 실패
    
    Examples:
        >>> button = find_pdf_button(driver)
        >>> path = download_pdf(driver, button, "/output", "test.pdf")
        INFO: ✅ [detector_cdp] Blob URL 다운로드 성공: /output/test.pdf
    """
    controller = PDFDetectorController(driver, log_attempts)
    return controller.download(button, folder_path, filename, node_name)


# Public API
__all__ = [
    'find_pdf_button',
    'download_pdf',
    'get_button_info',
    'validate_button',
]
