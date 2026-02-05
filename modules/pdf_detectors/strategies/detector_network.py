#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Network 방식 PDF 다운로드
- 직접 PDF URL 다운로드
- requests 라이브러리 사용
"""

import logging
import os
import requests

logger = logging.getLogger(__name__)


class NetworkDetector:
    """네트워크 직접 다운로드"""
    
    NAME = "Network"
    PRIORITY = 2
    DESCRIPTION = "직접 PDF URL을 requests로 다운로드"
    
    def detect(self, driver):
        """
        직접 PDF URL인지 확인
        
        Returns:
            bool: 직접 PDF URL이면 True
        """
        try:
            current_url = driver.current_url
            return (
                current_url.endswith('.pdf') or 
                '.pdf?' in current_url or
                'pdf' in current_url.lower()
            ) and not current_url.startswith('blob:')
        except:
            return False
    
    def download(self, driver, folder_path, filename, node_name="Unknown"):
        """
        직접 URL로 PDF 다운로드
        
        Args:
            driver: Selenium WebDriver
            folder_path: 저장 폴더 경로
            filename: 파일명
            node_name: 노드 이름 (로그용)
        
        Returns:
            str: 저장된 파일 경로 또는 None
        """
        try:
            url = driver.current_url
            
            if not self.detect(driver):
                logger.debug(f"  ✗ 직접 PDF URL이 아님")
                return None
            
            logger.info(f"  📄 직접 PDF URL 감지 → Network 다운로드")
            logger.info(f"     URL: {url[:80]}...")
            
            # 세션에서 쿠키 가져오기
            cookies = driver.get_cookies()
            session = requests.Session()
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            # PDF 다운로드
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            # 파일 저장
            pdf_path = os.path.join(folder_path, filename)
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            logger.info(f"  ✅ PDF 저장 완료: {filename} ({file_size:,} bytes)")
            
            return pdf_path
        
        except Exception as e:
            logger.error(f"  ❌ Network PDF 다운로드 실패: {e}")
            return None
