#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Retrieval Strategy: Network
- requests 라이브러리를 사용한 PDF 회수
- 직접 PDF URL이 존재하는 경우
"""

import os
import time
import logging
import requests
from .button_strategies import BUTTON_STRATEGY_REGISTRY, BUTTON_STRATEGY_ORDER

logger = logging.getLogger(__name__)


class RetrievalNetwork:
    """Network 트래픽을 통한 PDF 회수"""
    
    def __init__(self):
        self.name = "retrieval_network"
        self.priority = 2
    
    def _find_button(self, driver):
        """버튼 찾기 (내부 구현 - 조용히)"""
        for strategy_name in BUTTON_STRATEGY_ORDER:
            strategy = BUTTON_STRATEGY_REGISTRY[strategy_name]
            try:
                button = strategy.find(driver)
                if button:
                    return button
            except:
                continue
        return None
    
    def download(self, driver, folder_path, filename, node_name="Unknown", log_attempts=False):
        """
        Network로 PDF 다운로드
        
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
            
            # 2. 현재 창 정보 저장
            original_window = driver.current_window_handle
            windows_before = driver.window_handles
            
            # 3. 버튼 클릭
            button.click()
            time.sleep(2)
            
            if log_attempts:
                logger.info(f"      ├─ 버튼 클릭: 완료")
            
            # 4. 새 창 확인
            windows_after = driver.window_handles
            new_window_opened = len(windows_after) > len(windows_before)
            
            pdf_url = None
            if new_window_opened:
                new_windows = [w for w in windows_after if w not in windows_before]
                if new_windows:
                    driver.switch_to.window(new_windows[0])
                    pdf_url = driver.current_url
                    
                    if log_attempts:
                        logger.info(f"      ├─ 새 창 URL: {pdf_url[:50]}...")
            
            # 5. URL 체크
            if not pdf_url:
                if log_attempts:
                    logger.warning(f"      └─ PDF URL 없음")
                return None
            
            # Blob URL은 Network로 다운로드 불가
            if pdf_url.startswith("blob:"):
                if log_attempts:
                    logger.warning(f"      └─ Blob URL은 Network로 불가")
                
                # 정리
                if new_window_opened:
                    driver.close()
                    driver.switch_to.window(original_window)
                
                return None
            
            # PDF URL 체크
            if not (pdf_url.endswith('.pdf') or 'pdf' in pdf_url.lower()):
                if log_attempts:
                    logger.warning(f"      └─ PDF URL 아님")
                
                # 정리
                if new_window_opened:
                    driver.close()
                    driver.switch_to.window(original_window)
                
                return None
            
            # 6. requests로 다운로드
            try:
                # Selenium 쿠키 가져오기
                cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
                
                response = requests.get(pdf_url, cookies=cookies, timeout=30)
                response.raise_for_status()
                
                pdf_path = os.path.join(folder_path, filename)
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = len(response.content)
                
                if log_attempts:
                    logger.info(f"      └─ Network 저장: 성공 ({file_size:,} bytes)")
                
                # 정리
                if new_window_opened:
                    driver.close()
                    driver.switch_to.window(original_window)
                
                return pdf_path
            
            except Exception as e:
                if log_attempts:
                    logger.error(f"      └─ Network 저장 실패: {e}")
                
                # 정리
                if new_window_opened:
                    try:
                        driver.close()
                        driver.switch_to.window(original_window)
                    except:
                        pass
                
                return None
        
        except Exception as e:
            if log_attempts:
                logger.error(f"      └─ 오류: {e}")
            return None
