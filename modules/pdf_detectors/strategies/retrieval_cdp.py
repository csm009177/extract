#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Retrieval Strategy: CDP printToPDF
- Chrome DevTools Protocol의 Page.printToPDF 사용
- 전체 페이지를 1개 PDF로 빠르게 생성 (벡터 기반)
"""

import os
import base64
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from .button_strategies import BUTTON_STRATEGY_REGISTRY, BUTTON_STRATEGY_ORDER

logger = logging.getLogger(__name__)


class RetrievalCDP:
    """Page.printToPDF로 전체 페이지를 1개 PDF로 생성 (빠름, 벡터 기반)"""
    
    def __init__(self):
        self.name = "retrieval_cdp"
        self.priority = 3  # 3순위
    
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
    
    def _save_pdf_with_cdp(self, driver, output_path, log_attempts=False):
        """
        Chrome의 Page.printToPDF로 전체 페이지를 1개 PDF로 저장
        
        Args:
            driver: Selenium WebDriver
            output_path: PDF 저장 경로
            log_attempts: 로그 출력 여부
            
        Returns:
            str: 성공 시 파일 경로, 실패 시 None
        """
        try:
            # 1. 전체 페이지 높이 측정
            total_height = driver.execute_script("""
                return Math.max(
                    document.body.scrollHeight,
                    document.documentElement.scrollHeight,
                    document.body.offsetHeight,
                    document.documentElement.offsetHeight
                );
            """)
            
            viewport_width = driver.execute_script("return window.innerWidth")
            
            if log_attempts:
                logger.info(f"      ├─ 페이지 크기: {viewport_width}x{total_height}px")
            
            # 2. lazy load 이미지 강제 로딩
            driver.execute_script("""
                document.querySelectorAll('img[loading="lazy"]').forEach(img => {
                    img.loading = 'eager';
                });
            """)
            time.sleep(0.5)  # 이미지 로딩 대기
            
            # 3. 스크롤을 최하단까지 내려서 모든 콘텐츠 로드
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            driver.execute_script("window.scrollTo(0, 0);")  # 다시 상단으로
            time.sleep(0.3)
            
            # 4. Paper 크기 계산 (px → cm, 96 DPI 기준)
            # 1 inch = 2.54 cm, 96 DPI = 96 px/inch
            # 너비는 A4 표준(21cm)으로 고정, 높이만 콘텐츠에 맞춤
            paper_width_cm = 21.0  # A4 너비 고정 (8.27 inches)
            paper_height_cm = (total_height / 96) * 2.54
            
            # 5. CDP로 PDF 생성
            if log_attempts:
                logger.info(f"      ├─ PDF 생성 시작 (Page.printToPDF)")
                logger.info(f"         └─ Paper 크기: {paper_width_cm:.2f} x {paper_height_cm:.2f} cm (A4 너비 고정)")
            
            result = driver.execute_cdp_cmd("Page.printToPDF", {
                "printBackground": True,
                "paperWidth": paper_width_cm,
                "paperHeight": paper_height_cm,
                "marginTop": 0,
                "marginBottom": 0,
                "marginLeft": 0,
                "marginRight": 0,
                "scale": 1.0,
                "displayHeaderFooter": False,
                "preferCSSPageSize": False,
            })
            
            # 6. PDF 데이터 저장
            pdf_data = base64.b64decode(result['data'])
            
            with open(output_path, 'wb') as f:
                f.write(pdf_data)
            
            file_size = len(pdf_data)
            
            if log_attempts:
                logger.info(f"      └─ PDF 생성 완료: {file_size:,} bytes")
            
            return output_path
            
        except Exception as e:
            if log_attempts:
                logger.error(f"      └─ PDF 생성 실패: {e}")
            return None
    
    def detect(self, driver):
        """버튼 찾기 (외부 인터페이스 - 로깅 있음)"""
        return self._find_button(driver)
    
    def download(self, driver, folder_path, filename, node_name="Unknown", log_attempts=False):
        """
        CDP Page.printToPDF로 PDF 다운로드
        
        Args:
            driver: Selenium WebDriver
            folder_path: 저장할 폴더 경로
            filename: PDF 파일명
            node_name: 노드 이름 (로그용, 사용 안 함)
            log_attempts: 로깅 여부
            
        Returns:
            str: 성공 시 파일 경로, 실패 시 None
        """
        try:
            # 1. 버튼 찾기
            button = self._find_button(driver)
            
            if not button:
                if log_attempts:
                    logger.warning(f"      ├─ 버튼 찾기 실패")
                return None
            
            if log_attempts:
                logger.info(f"      ├─ 버튼 찾기: 성공")
            
            # 2. 현재 URL 저장 (새 창이 아니라 URL 변경 감지)
            original_window = driver.current_window_handle
            original_url = driver.current_url
            
            # 3. 버튼 클릭
            button.click()
            
            if log_attempts:
                logger.info(f"      ├─ 버튼 클릭: 완료")
            
            # 4. URL 변경 대기 (새 창이 아니라 location.href 방식)
            try:
                # IsPrint=true 파라미터가 추가된 페이지로 이동 대기 (최대 10초)
                WebDriverWait(driver, 10).until(
                    lambda d: "IsPrint=true" in d.current_url or d.current_url != original_url
                )
                time.sleep(2)  # 페이지 로딩 완료 대기
                
                if log_attempts:
                    logger.info(f"      ├─ PDF 페이지 로딩: 완료")
            except:
                # URL이 변경되지 않았다면 그대로 진행
                time.sleep(2)
                if log_attempts:
                    logger.warning(f"      ├─ URL 변경 없음 (그대로 진행)")
            
            # 5. PDF 생성
            os.makedirs(folder_path, exist_ok=True)
            pdf_path = os.path.join(folder_path, filename)
            
            result = self._save_pdf_with_cdp(driver, pdf_path, log_attempts)
            
            if not result:
                if log_attempts:
                    logger.error(f"      └─ PDF 생성 실패")
                return None
            
            # 6. 정리 - URL이 변경되었다면 뒤로 가기
            if driver.current_url != original_url:
                try:
                    driver.back()
                    time.sleep(1)
                    if log_attempts:
                        logger.info(f"      └─ 원본 페이지로 복귀: 완료")
                except Exception as e:
                    if log_attempts:
                        logger.warning(f"      └─ 페이지 복귀 실패: {e}")
            
            return result
            
        except Exception as e:
            if log_attempts:
                logger.error(f"      └─ 오류: {e}")
            
            # 정리 - 오류 발생 시에도 원본 페이지로 복귀
            try:
                if driver.current_url != original_url:
                    driver.back()
                    time.sleep(1)
            except:
                pass
            
            return None
