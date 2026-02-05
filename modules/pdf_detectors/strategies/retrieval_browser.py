#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Retrieval Strategy: Browser Download
- 브라우저 다운로드 폴더 모니터링을 통한 PDF 회수
- 자동 다운로드가 설정된 경우
"""

import os
import time
import logging
import shutil
from pathlib import Path
from .button_strategies import BUTTON_STRATEGY_REGISTRY, BUTTON_STRATEGY_ORDER

logger = logging.getLogger(__name__)


class RetrievalBrowser:
    """브라우저 다운로드 폴더 모니터링을 통한 PDF 회수"""
    
    def __init__(self):
        self.name = "retrieval_browser"
        self.priority = 3  # 최후 수단
    
    def _find_button(self, driver):
        """버튼 찾기 (내부 구현 - 조용히)"""
        for strategy_name in BUTTON_STRATEGY_ORDER:
            strategy = BUTTON_STRATEGY_REGISTRY[strategy_name]
            try:
                button = strategy.detect(driver)  # ✅ find → detect
                if button:
                    return button
            except:
                continue
        return None
    
    def download(self, driver, folder_path, filename, node_name="Unknown", log_attempts=False):
        """
        브라우저 다운로드 폴더에서 PDF 회수
        
        Args:
            driver: Selenium WebDriver
            folder_path: 저장 폴더
            filename: 파일명
            node_name: 노드 이름
            log_attempts: 로그 출력 여부
        
        Returns:
            str: 저장된 파일 경로 또는 None
        """
        try:
            # 1. 버튼 찾기 (조용히)
            button = self._find_button(driver)
            
            if not button:
                if log_attempts:
                    logger.warning(f"      ├─ 버튼 찾기 실패")
                return None
            
            if log_attempts:
                logger.info(f"      ├─ 버튼 찾기: 성공")
            
            # 2. 다운로드 폴더 확인
            download_folder = os.path.expanduser("~\\Downloads")
            
            # 기존 .pdf 파일 목록
            existing_files = set()
            if os.path.exists(download_folder):
                existing_files = {
                    f for f in os.listdir(download_folder) 
                    if f.endswith('.pdf')
                }
            
            # 3. 버튼 클릭
            button.click()
            
            if log_attempts:
                logger.info(f"      ├─ 버튼 클릭: 완료")
                logger.info(f"      ├─ 다운로드 폴더 모니터링 시작...")
            
            # 4. 새 파일 대기 (최대 10초)
            max_wait = 10
            start_time = time.time()
            new_file = None
            
            while time.time() - start_time < max_wait:
                time.sleep(0.5)
                
                if not os.path.exists(download_folder):
                    continue
                
                current_files = {
                    f for f in os.listdir(download_folder) 
                    if f.endswith('.pdf') and not f.endswith('.crdownload')
                }
                
                new_files = current_files - existing_files
                if new_files:
                    new_file = list(new_files)[0]
                    break
            
            if not new_file:
                if log_attempts:
                    logger.warning(f"      └─ 다운로드 파일 감지 실패 (10초 timeout)")
                return None
            
            # 5. 파일 이동
            try:
                source_path = os.path.join(download_folder, new_file)
                target_path = os.path.join(folder_path, filename)
                
                # 대상 폴더가 없으면 생성
                os.makedirs(folder_path, exist_ok=True)
                
                # 파일 이동
                shutil.move(source_path, target_path)
                
                file_size = os.path.getsize(target_path)
                
                if log_attempts:
                    logger.info(f"      └─ Browser 저장: 성공 ({file_size:,} bytes)")
                
                return target_path
            
            except Exception as e:
                if log_attempts:
                    logger.error(f"      └─ 파일 이동 실패: {e}")
                return None
        
        except Exception as e:
            if log_attempts:
                logger.error(f"      └─ 오류: {e}")
            return None
