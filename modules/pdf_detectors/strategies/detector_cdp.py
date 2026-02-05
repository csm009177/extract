#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CDP (Chrome DevTools Protocol) 방식 PDF 다운로드
- Blob URL 처리
- Page.printToPDF 사용
"""

import logging
import base64
import os
import time

logger = logging.getLogger(__name__)


class CDPDetector:
    """CDP를 사용한 PDF 다운로드"""
    
    NAME = "CDP"
    PRIORITY = 1
    DESCRIPTION = "Chrome DevTools Protocol로 Blob URL PDF 다운로드"
    
    def detect(self, driver):
        """
        CDP 사용 가능 여부 확인
        
        Returns:
            bool: CDP 사용 가능하면 True
        """
        try:
            # CDP 명령 테스트
            driver.execute_cdp_cmd("Browser.getVersion", {})
            return True
        except Exception as e:
            logger.debug(f"CDP 사용 불가: {e}")
            return False
    
    def download(self, driver, folder_path, filename, node_name="Unknown"):
        """
        CDP로 PDF 다운로드
        
        Args:
            driver: Selenium WebDriver (새 창으로 전환된 상태)
            folder_path: 저장 폴더 경로
            filename: 파일명
            node_name: 노드 이름 (로그용)
        
        Returns:
            str: 저장된 파일 경로 또는 None
        """
        try:
            current_url = driver.current_url
            
            if not current_url.startswith("blob:"):
                logger.debug(f"  ✗ Blob URL이 아님: {current_url[:50]}...")
                return None
            
            logger.info(f"  📄 Blob URL 감지 → CDP 사용")
            
            # CDP로 PDF 생성
            result = driver.execute_cdp_cmd("Page.printToPDF", {
                "printBackground": True,
                "paperWidth": 8.27,
                "paperHeight": 11.69,
                "preferCSSPageSize": True
            })
            
            # Base64 디코딩
            pdf_data = base64.b64decode(result['data'])
            
            # 파일 저장
            pdf_path = os.path.join(folder_path, filename)
            with open(pdf_path, 'wb') as f:
                f.write(pdf_data)
            
            file_size = len(pdf_data)
            logger.info(f"  ✅ PDF 저장 완료: {filename} ({file_size:,} bytes)")
            
            return pdf_path
        
        except Exception as e:
            logger.error(f"  ❌ CDP PDF 다운로드 실패: {e}")
            return None
