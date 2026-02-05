#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Detectors Package
- PDF 버튼 탐지 및 다운로드 기능 제공
"""

from .button_finder import ButtonFinder
from .retrieval_controller import PDFRetrievalController, RETRIEVAL_STRATEGIES


def download_pdf(driver, folder_path, filename, node_name=None, log_attempts=True, selected_strategies=None):
    """
    PDF 다운로드 편의 함수
    
    Args:
        driver: Selenium WebDriver
        folder_path: 저장 폴더 경로
        filename: 파일명
        node_name: 노드 이름 (로깅용)
        log_attempts: 시도 로그 출력 여부
        selected_strategies: 사용할 전략 리스트 (예: ["browser", "cdp_print"])
    
    Returns:
        str: 다운로드된 PDF 경로 또는 None
    """
    controller = PDFRetrievalController(
        driver=driver,
        log_attempts=log_attempts,
        order=selected_strategies
    )
    
    return controller.download(
        folder_path=folder_path,
        filename=filename,
        node_name=node_name
    )


__all__ = ['ButtonFinder', 'PDFRetrievalController', 'RETRIEVAL_STRATEGIES', 'download_pdf']