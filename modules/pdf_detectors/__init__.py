#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Detectors 모듈 - 진입점
- find_pdf_button: PDF 버튼 찾기 (8가지 버튼 전략 사용)
- download_pdf: PDF 다운로드 (3가지 retrieval 전략 자동 선택)

Usage:
    from modules.pdf_detectors import find_pdf_button, download_pdf
    
    # 1단계: 버튼 찾기 (선택사항 - download_pdf가 내부에서 자동 처리)
    button = find_pdf_button(driver)
    
    # 2단계: PDF 다운로드 (3가지 retrieval 방식 자동 시도)
    path = download_pdf(driver, "/output", "test.pdf")
"""

from .button_finder import ButtonFinder
from .retrieval_controller import PDFRetrievalController
from .utils import get_button_info, validate_button


def find_pdf_button(driver, strategy="auto", log_attempts=True):
    """
    PDF 버튼 찾기 (8가지 버튼 전략 사용)
    
    NOTE: download_pdf()가 내부에서 자동으로 버튼을 찾으므로,
          이 함수를 직접 호출할 필요는 없습니다.
    
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
    """
    finder = ButtonFinder(driver, log_attempts)
    return finder.find(strategy)


def download_pdf(driver, folder_path, filename, node_name="Unknown", log_attempts=True):
    """
    PDF 다운로드 (3가지 retrieval 방식 자동 시도)
    
    Controller가 순차적으로 시도:
        [1/3] retrieval_cdp 시도...
              ├─ 버튼 찾기: 성공 (내부에서 자동 처리)
              ├─ 버튼 클릭: 완료
              ├─ 새 창 감지: blob:...
              └─ CDP 저장: 성공 ✅
        
        (성공하면 다음 전략 시도 안 함)
    
    Args:
        driver: Selenium WebDriver
        folder_path: str - 저장 폴더 경로
        filename: str - 파일명 (예: "example.pdf")
        node_name: str - 노드 이름 (로그용)
        log_attempts: bool - 시도 과정 로그 출력 여부
    
    Returns:
        str: 저장된 파일 경로
        None: 다운로드 실패
    
    Examples:
        >>> path = download_pdf(driver, "/output", "test.pdf")
        INFO: [1/3] retrieval_cdp 시도...
        INFO:   ├─ 버튼 찾기: 성공
        INFO:   ├─ 버튼 클릭: 완료
        INFO:   └─ CDP 저장: 성공 (12,345 bytes)
    """
    controller = PDFRetrievalController(driver, log_attempts)
    return controller.download(folder_path, filename, node_name)


# Public API
__all__ = [
    'find_pdf_button',
    'download_pdf',
    'get_button_info',
    'validate_button',
]
