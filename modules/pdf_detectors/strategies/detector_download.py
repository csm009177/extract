#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
브라우저 다운로드 폴더 모니터링 방식
- 자동 다운로드 감지
- 파일 이동
"""

import logging
import os
import time
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class DownloadDetector:
    """브라우저 다운로드 폴더 모니터링"""
    
    NAME = "Download"
    PRIORITY = 3
    DESCRIPTION = "브라우저 자동 다운로드 폴더 모니터링"
    
    def __init__(self, download_folder=None):
        """
        Args:
            download_folder: Chrome 다운로드 폴더 경로
        """
        self.download_folder = download_folder or str(Path.home() / "Downloads")
    
    def detect(self, driver):
        """
        자동 다운로드 가능 여부 확인
        
        Returns:
            bool: 항상 True (fallback)
        """
        return True
    
    def wait_for_download(self, timeout=30):
        """
        새 PDF 파일이 다운로드될 때까지 대기
        
        Args:
            timeout: 최대 대기 시간 (초)
        
        Returns:
            str: 다운로드된 파일 경로 또는 None
        """
        start_time = time.time()
        
        # 다운로드 전 파일 목록
        before_files = set(os.listdir(self.download_folder))
        
        while time.time() - start_time < timeout:
            time.sleep(1)
            
            current_files = set(os.listdir(self.download_folder))
            new_files = current_files - before_files
            
            for file in new_files:
                if file.endswith('.pdf') and not file.endswith('.crdownload'):
                    file_path = os.path.join(self.download_folder, file)
                    logger.debug(f"  ✓ 새 PDF 파일 감지: {file}")
                    return file_path
        
        logger.debug(f"  ✗ 다운로드 타임아웃 ({timeout}초)")
        return None
    
    def download(self, driver, folder_path, filename, node_name="Unknown"):
        """
        다운로드 폴더에서 PDF 파일 찾아서 이동
        
        Args:
            driver: Selenium WebDriver
            folder_path: 저장 폴더 경로
            filename: 파일명
            node_name: 노드 이름 (로그용)
        
        Returns:
            str: 저장된 파일 경로 또는 None
        """
        try:
            logger.info(f"  📄 다운로드 폴더 모니터링 시작...")
            
            # 새 파일 대기
            downloaded_file = self.wait_for_download(timeout=30)
            
            if not downloaded_file:
                logger.warning(f"  ⚠️  다운로드된 파일을 찾을 수 없음")
                return None
            
            # 파일 이동
            target_path = os.path.join(folder_path, filename)
            shutil.move(downloaded_file, target_path)
            
            file_size = os.path.getsize(target_path)
            logger.info(f"  ✅ PDF 저장 완료: {filename} ({file_size:,} bytes)")
            
            return target_path
        
        except Exception as e:
            logger.error(f"  ❌ Download PDF 저장 실패: {e}")
            return None
