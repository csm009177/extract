#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Detector Controller
- PDF 다운로드 방식 자동 판단 및 실행
- 상황에 맞는 최적의 detector 선택
"""

import logging
import time
from .strategies import DOWNLOAD_STRATEGY_REGISTRY, DOWNLOAD_STRATEGY_ORDER

logger = logging.getLogger(__name__)


class PDFDetectorController:
    """PDF 다운로드 방식 자동 선택 및 실행"""
    
    def __init__(self, driver, log_attempts=True):
        self.driver = driver
        self.log_attempts = log_attempts
        
        if log_attempts:
            logger.info(f"  🔌 PDF Detector Controller 초기화")
            logger.info(f"     - 등록된 다운로드 전략: {len(DOWNLOAD_STRATEGY_REGISTRY)}개")
    
    def _analyze_situation(self, original_window):
        """
        현재 상황 분석
        
        Returns:
            dict: 상황 정보
        """
        situation = {
            "new_window_opened": False,
            "new_window_handle": None,
            "url": None,
            "url_is_blob": False,
            "url_is_pdf": False,
        }
        
        try:
            current_windows = self.driver.window_handles
            
            # 새 창이 열렸는지 확인
            if len(current_windows) > 1:
                situation["new_window_opened"] = True
                
                # 새 창 찾기
                for handle in current_windows:
                    if handle != original_window:
                        situation["new_window_handle"] = handle
                        
                        # 새 창으로 전환
                        self.driver.switch_to.window(handle)
                        time.sleep(1)
                        
                        # URL 확인
                        url = self.driver.current_url
                        situation["url"] = url
                        situation["url_is_blob"] = url.startswith("blob:")
                        situation["url_is_pdf"] = (
                            url.endswith('.pdf') or 
                            '.pdf?' in url or
                            'pdf' in url.lower()
                        )
                        
                        break
        except Exception as e:
            logger.debug(f"상황 분석 중 오류: {e}")
        
        return situation
    
    def select_strategy(self, situation):
        """
        상황에 맞는 최적의 전략 선택
        
        Args:
            situation: dict - 상황 정보
        
        Returns:
            list: 시도할 전략 이름 리스트
        """
        strategies = []
        
        # 새 창 + Blob URL → CDP 우선
        if situation["new_window_opened"] and situation["url_is_blob"]:
            strategies.append("cdp")
            logger.info(f"  📊 상황 분석: 새 창 + Blob URL → CDP 우선")
        
        # 새 창 + 직접 PDF URL → Network 우선
        elif situation["new_window_opened"] and situation["url_is_pdf"]:
            strategies.append("network")
            logger.info(f"  📊 상황 분석: 새 창 + PDF URL → Network 우선")
        
        # 새 창이 안 열림 → Download 폴더 모니터링
        elif not situation["new_window_opened"]:
            strategies.append("download")
            logger.info(f"  📊 상황 분석: 새 창 없음 → Download 폴더 모니터링")
        
        # 나머지 전략도 추가 (Fallback)
        for strategy_name in DOWNLOAD_STRATEGY_ORDER:
            if strategy_name not in strategies:
                strategies.append(strategy_name)
        
        return strategies
    
    def download(self, button, folder_path, filename, node_name="Unknown"):
        """
        PDF 다운로드 실행
        
        Args:
            button: WebElement - PDF 버튼
            folder_path: str - 저장 폴더 경로
            filename: str - 파일명
            node_name: str - 노드 이름 (로그용)
        
        Returns:
            str: 저장된 파일 경로 또는 None
        """
        try:
            # 현재 창 저장
            original_window = self.driver.current_window_handle
            
            # 버튼 클릭
            logger.info(f"  🖱️  PDF 버튼 클릭")
            button.click()
            time.sleep(3)
            
            # 상황 분석
            situation = self._analyze_situation(original_window)
            
            if self.log_attempts:
                logger.info(f"  📊 다운로드 상황 분석")
                logger.info(f"     - 새 창 열림: {'✓' if situation['new_window_opened'] else '✗'}")
                if situation['url']:
                    logger.info(f"     - URL: {situation['url'][:60]}...")
                    logger.info(f"     - Blob URL: {'✓' if situation['url_is_blob'] else '✗'}")
                    logger.info(f"     - PDF URL: {'✓' if situation['url_is_pdf'] else '✗'}")
            
            # 최적 전략 선택
            strategies = self.select_strategy(situation)
            
            # 전략 실행
            if self.log_attempts:
                logger.info(f"  🎯 다운로드 전략 실행")
            
            result_path = None
            for idx, strategy_name in enumerate(strategies, 1):
                if self.log_attempts:
                    logger.info(f"     [{idx}/{len(strategies)}] {strategy_name} 시도...")
                
                try:
                    detector = DOWNLOAD_STRATEGY_REGISTRY.get(strategy_name)
                    if not detector:
                        logger.warning(f"     ⚠️  알 수 없는 전략: {strategy_name}")
                        continue
                    
                    # 전략 사용 가능 여부 확인
                    if not detector.detect(self.driver):
                        logger.debug(f"     ✗ {strategy_name} 사용 불가")
                        continue
                    
                    # 다운로드 실행
                    result_path = detector.download(
                        self.driver, 
                        folder_path, 
                        filename, 
                        node_name
                    )
                    
                    if result_path:
                        if self.log_attempts:
                            logger.info(f"     ✅ 다운로드 성공!")
                            logger.info(f"        [전략] {strategy_name} ({detector.NAME})")
                            logger.info(f"        [파일] {result_path}")
                        break
                
                except Exception as e:
                    logger.error(f"     ❌ {strategy_name} 오류: {e}")
            
            # 원래 창으로 복귀
            if situation["new_window_opened"] and situation["new_window_handle"]:
                try:
                    self.driver.close()  # 새 창 닫기
                    self.driver.switch_to.window(original_window)
                    logger.info(f"  📌 원래 창으로 복귀")
                except:
                    pass
            
            if not result_path and self.log_attempts:
                logger.warning(f"  ⚠️  모든 전략 실패 - PDF를 다운로드할 수 없습니다")
            
            return result_path
        
        except Exception as e:
            logger.error(f"  ❌ PDF 다운로드 중 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
