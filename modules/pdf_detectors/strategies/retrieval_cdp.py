#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Retrieval Strategy: CDP
- Chrome DevTools Protocol을 사용한 PDF 회수
- Blob URL, 렌더링된 페이지 등 CDP로 저장 가능한 모든 경우
"""

import os
import base64
import time
import logging
from .button_strategies import BUTTON_STRATEGY_REGISTRY, BUTTON_STRATEGY_ORDER

logger = logging.getLogger(__name__)


class RetrievalCDP:
    """CDP Page.printToPDF를 사용한 PDF 회수"""
    
    def __init__(self):
        self.name = "retrieval_cdp"
        self.priority = 1  # 최우선
    
    def _find_button(self, driver):
        """버튼 찾기 (내부 구현 - 조용히)"""
        for strategy_name in BUTTON_STRATEGY_ORDER:
            strategy = BUTTON_STRATEGY_REGISTRY[strategy_name]
            try:
                button = strategy.detect(driver)
                if button:
                    return button
            except:
                continue
        return None
    
    def download(self, driver, folder_path, filename, node_name="Unknown", log_attempts=False):
        """
        CDP로 PDF 다운로드
        
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
            # 1. 버튼 찾기 (조용히 - 로그 출력 안함)
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
            
            target_window = original_window
            if new_window_opened:
                new_windows = [w for w in windows_after if w not in windows_before]
                if new_windows:
                    target_window = new_windows[0]
                    driver.switch_to.window(target_window)
                    
                    if log_attempts:
                        logger.info(f"      ├─ 새 창 감지: {driver.current_url[:50]}...")
            
            # 5. CDP로 PDF 저장
            try:
                result = driver.execute_cdp_cmd("Page.printToPDF", {
                    "printBackground": True,
                    "paperWidth": 8.27,
                    "paperHeight": 11.69,
                    "preferCSSPageSize": True
                })
                
                pdf_data = base64.b64decode(result['data'])
                pdf_path = os.path.join(folder_path, filename)
                
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_data)
                
                file_size = len(pdf_data)
                
                if log_attempts:
                    logger.info(f"      └─ CDP 저장: 성공 ({file_size:,} bytes)")
                
                # 6. 정리
                if new_window_opened:
                    driver.close()
                    driver.switch_to.window(original_window)
                
                return pdf_path
            
            except Exception as e:
                if log_attempts:
                    logger.error(f"      └─ CDP 저장 실패: {e}")
                
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
