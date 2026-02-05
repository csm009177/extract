#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Retrieval Controller
- PDF 회수 방식 자동 판단 및 실행
- 3가지 retrieval 방식 순차 시도
"""

import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .strategies import DOWNLOAD_STRATEGY_REGISTRY, DOWNLOAD_STRATEGY_ORDER

logger = logging.getLogger(__name__)


class PDFRetrievalController:
    """PDF 회수 방식 자동 선택 및 실행"""
    
    def __init__(self, driver, log_attempts=True):
        self.driver = driver
        self.log_attempts = log_attempts
        
        if log_attempts:
            logger.info(f"  🎯 PDF Retrieval Controller 초기화")
            logger.info(f"     - 등록된 회수 전략: {len(DOWNLOAD_STRATEGY_REGISTRY)}개")
    
    def download(self, folder_path, filename, node_name="Unknown", check_session=True):
        """
        PDF 다운로드 (3가지 retrieval 방식 순차 시도)
        
        Args:
            folder_path: 저장 폴더 경로
            filename: 파일명
            node_name: 노드 이름 (로그용)
            check_session: bool - 세션 확인 여부
        
        Returns:
            str: 저장된 파일 경로 또는 None
        """
        # 세션 확인 (세션 만료 대비)
        if check_session:
            session_valid = self._check_session()
            if self.log_attempts:
                logger.info(f"  🔐 세션 확인: {'✅ 유효' if session_valid else '❌ 만료'}")
            
            if not session_valid:
                if self.log_attempts:
                    logger.error(f"  ❌ 세션 만료 - 재로그인 필요")
                return None
        
        if self.log_attempts:
            logger.info(f"  🔍 PDF 다운로드 시도: {node_name}")
            logger.info(f"     - 저장 경로: {folder_path}/{filename}")
        
        # 전략 순서대로 시도
        for idx, strategy_name in enumerate(DOWNLOAD_STRATEGY_ORDER, 1):
            strategy = DOWNLOAD_STRATEGY_REGISTRY[strategy_name]
            
            # 전략 이름을 사용자 친화적으로 변환
            strategy_display_name = {
                'retrieval_cdp': 'CDP (Page.printToPDF)',
                'retrieval_network': 'Network (HTTP 요청)',
                'retrieval_browser': 'Browser (다운로드 폴더)'
            }.get(strategy_name, strategy_name)
            
            if self.log_attempts:
                logger.info(f"  📌 [{idx}/{len(DOWNLOAD_STRATEGY_ORDER)}] {strategy_display_name} 시도...")
            
            try:
                # 각 retrieval 전략 실행 (내부에서 버튼 찾기부터 다운로드까지 모두 처리)
                result = strategy.download(
                    driver=self.driver,
                    folder_path=folder_path,
                    filename=filename,
                    node_name=node_name,
                    log_attempts=self.log_attempts
                )
                
                if result:
                    if self.log_attempts:
                        logger.info(f"  ✅ {strategy_display_name} 성공: {result}")
                    return result
                
                if self.log_attempts:
                    logger.warning(f"  ⚠️  {strategy_display_name} 실패 - 다음 전략 시도")
            
            except Exception as e:
                if self.log_attempts:
                    logger.error(f"  ❌ {strategy_display_name} 오류: {e}")
                continue
        
        # 모든 전략 실패
        if self.log_attempts:
            logger.error(f"  ❌ 모든 retrieval 전략 실패")
        return None
    
    def _check_session(self):
        """세션 유효성 확인 (세션 만료 대비)"""
        try:
            # 현재 URL 확인
            current_url = self.driver.current_url
            
            if self.log_attempts:
                logger.info(f"     🔍 현재 URL: {current_url[:80]}")
            
            # 🆕 중복 로그인 대화상자 감지 및 처리
            if "DialogExistLoginSession" in current_url:
                if self.log_attempts:
                    logger.warning(f"     ⚠️  중복 로그인 대화상자 감지 - 자동 처리")
                try:
                    if self.log_attempts:
                        logger.info(f"     🔍 대화상자 HTML 분석 중...")
                    
                    # 여러 가능한 버튼 찾기
                    button_selectors = [
                        (By.ID, "ctl00_BodyContentPlaceHolder_lbtYes"),  # ⭐ 실제 ID
                        (By.ID, "btnYes"),
                        (By.ID, "Button1"),  # ASP.NET 기본
                        (By.ID, "btnOK"),
                        (By.ID, "btnConfirm"),
                        (By.NAME, "btnYes"),
                        (By.XPATH, "//a[contains(@onclick, 'lbtYesClick')]"),  # ⭐ onclick 함수
                        (By.XPATH, "//a[contains(@class, 'MainButton')]"),  # ⭐ CSS 클래스
                        (By.XPATH, "//input[@type='button' and contains(@value, '예')]"),
                        (By.XPATH, "//input[@type='button' and contains(@value, 'Yes')]"),
                        (By.XPATH, "//input[@type='button' and contains(@value, '확인')]"),
                        (By.XPATH, "//input[@type='button' and contains(@value, 'OK')]"),
                        (By.XPATH, "//input[@type='submit']"),
                        (By.XPATH, "//button[contains(text(), '예')]"),
                        (By.XPATH, "//button[contains(text(), 'Yes')]"),
                        (By.XPATH, "//a[contains(text(), '예')]"),
                        (By.XPATH, "//a[.//span[contains(text(), 'Yes')]]"),  # ⭐ span 안의 텍스트
                        (By.CSS_SELECTOR, "input[value*='예']"),
                    ]
                    
                    confirm_button = None
                    for by_type, selector in button_selectors:
                        try:
                            confirm_button = WebDriverWait(self.driver, 2).until(
                                EC.element_to_be_clickable((by_type, selector))
                            )
                            if self.log_attempts:
                                logger.info(f"     ✅ 버튼 발견: {by_type}={selector}")
                            break
                        except:
                            continue
                    
                    if not confirm_button:
                        # 페이지 소스 저장 (디버깅용)
                        import os
                        debug_dir = "debug_output"
                        os.makedirs(debug_dir, exist_ok=True)
                        
                        with open(f"{debug_dir}/duplicate_login_dialog.html", "w", encoding="utf-8") as f:
                            f.write(self.driver.page_source)
                        
                        if self.log_attempts:
                            logger.error(f"     ❌ 버튼을 찾을 수 없음 - HTML 저장: {debug_dir}/duplicate_login_dialog.html")
                            
                            # 모든 input/button 요소 출력
                            all_buttons = self.driver.find_elements(By.XPATH, "//input | //button | //a")
                            logger.info(f"     🔍 페이지의 모든 버튼/링크 ({len(all_buttons)}개):")
                            for btn in all_buttons[:10]:  # 처음 10개만
                                try:
                                    tag = btn.tag_name
                                    btn_id = btn.get_attribute('id') or 'None'
                                    btn_value = btn.get_attribute('value') or 'None'
                                    btn_text = btn.text or 'None'
                                    logger.info(f"        - <{tag}> id={btn_id} value={btn_value} text={btn_text}")
                                except:
                                    pass
                        
                        return False
                    
                    # 버튼 클릭
                    confirm_button.click()
                    time.sleep(2)
                    if self.log_attempts:
                        logger.info(f"     ✅ 중복 로그인 대화상자 처리 완료")
                    return True
                    
                except Exception as e:
                    if self.log_attempts:
                        logger.error(f"     ❌ 대화상자 처리 실패: {e}")
                    return False
            
            # 로그인 페이지로 리다이렉트되었는지 확인
            if "login" in current_url.lower() or "logon" in current_url.lower():
                if self.log_attempts:
                    logger.warning(f"     ⚠️  로그인 페이지 감지")
                return False
            
            # KR-CON 사이트에 정상적으로 접근 중인지 확인
            if "www.krs.co.kr" in current_url or "krcon.krs.co.kr" in current_url:
                # 세션 쿠키 확인 (선택적)
                cookies = self.driver.get_cookies()
                if self.log_attempts:
                    logger.info(f"     🍪 쿠키 개수: {len(cookies)}")
                
                if cookies:  # 쿠키가 있으면 OK
                    if self.log_attempts:
                        logger.info(f"     ✅ KR-CON 도메인 + 쿠키 존재")
                    return True
                
                # 쿠키가 없어도 KR-CON 사이트 내에 있으면 OK
                if self.log_attempts:
                    logger.info(f"     ✅ KR-CON 도메인 (쿠키 없음)")
                return True
            
            # 다른 도메인이면 세션 확인 실패
            if self.log_attempts:
                logger.warning(f"     ⚠️  비정상 도메인: {current_url[:50]}")
            return False
        
        except Exception as e:
            if self.log_attempts:
                logger.warning(f"  ⚠️  세션 확인 실패: {e}")
            return True  # 확인 실패 시 일단 통과
