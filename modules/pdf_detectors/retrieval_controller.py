#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Retrieval Controller
- PDF 회수 방식 자동 판단 및 실행
- 여러 retrieval 전략 순차 시도
"""

import logging
import time
import importlib
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


# ⭐⭐⭐ PDF 회수 전략 설정 (중앙 관리)
RETRIEVAL_STRATEGIES = {
    "network": {
        "enabled": False,  # ⭐ 기본 비활성화 (order로 활성화)
        "priority": 1,
        "module": "modules.pdf_detectors.strategies.retrieval_network",
        "class_name": "RetrievalNetwork",
        "display_name": "Network (HTTP 요청)",
        "description": "HTTP 직접 다운로드 - 원본 PDF",
    },
    "browser": {
        "enabled": False,  # ⭐ 기본 비활성화 (order로 활성화)
        "priority": 2,
        "module": "modules.pdf_detectors.strategies.retrieval_browser",
        "class_name": "RetrievalBrowser",
        "display_name": "Browser (다운로드 폴더)",
        "description": "브라우저 다운로드 - 원본 PDF",
    },
    "cdp_print": {
        "enabled": False,  # ⭐ 기본 비활성화 (order로 활성화)
        "priority": 3,
        "module": "modules.pdf_detectors.strategies.retrieval_cdp",
        "class_name": "RetrievalCDP",
        "display_name": "CDP printToPDF (빠름)",
        "description": "Chrome DevTools Protocol - 벡터 PDF",
    },
    "cdp_scroll": {
        "enabled": False,  # 기본 비활성화 (fallback)
        "priority": 4,
        "module": "modules.pdf_detectors.strategies.retrieval_cdp_scroll",
        "class_name": "RetrievalCDPScroll",
        "display_name": "CDP Scroll Screenshot (안전망)",
        "description": "스크롤 스크린샷 - 이미지 PDF",
    },
}


class PDFRetrievalController:
    """PDF 회수 방식 자동 선택 및 실행"""
    
    @staticmethod
    def override_strategies(enable=None, disable=None, order=None):
        """
        전략 설정 오버라이드
        
        Args:
            enable: list - 활성화할 전략
            disable: list - 비활성화할 전략
            order: list - 전략 순서 (이것만 활성화) ⭐
        
        Returns:
            dict: 수정된 전략 설정
        """
        import copy
        strategies = copy.deepcopy(RETRIEVAL_STRATEGIES)
        
        # ⭐ order가 있으면 해당 전략만 활성화 (나머지는 비활성화!)
        if order:
            # 모든 전략 먼저 비활성화
            for name in strategies:
                strategies[name]["enabled"] = False
            
            # order에 지정된 전략만 활성화 + 우선순위 부여
            for idx, name in enumerate(order, 1):
                if name in strategies:
                    strategies[name]["enabled"] = True
                    strategies[name]["priority"] = idx
            
            return strategies
        
        # order가 없으면 enable/disable 처리
        if enable:
            for name in enable:
                if name in strategies:
                    strategies[name]["enabled"] = True
        
        if disable:
            for name in disable:
                if name in strategies:
                    strategies[name]["enabled"] = False
        
        return strategies
    
    def __init_strategies(self, strategies_config):
        """전략 동적 로드 (내부 메서드)"""
        self.strategy_registry = {}
        self.active_strategies = []
        
        # enabled=True인 전략만 필터링
        enabled = {k: v for k, v in strategies_config.items() if v.get("enabled", False)}
        
        # priority 순으로 정렬
        sorted_strategies = sorted(enabled.items(), key=lambda x: x[1]["priority"])
        
        for name, config in sorted_strategies:
            try:
                # 동적 import
                module = importlib.import_module(config["module"])
                strategy_class = getattr(module, config["class_name"])
                
                # 인스턴스 생성 및 등록
                self.strategy_registry[name] = {
                    "instance": strategy_class(),
                    "config": config,
                }
                self.active_strategies.append(name)
                
                if self.log_attempts:
                    logger.info(f"     ✅ [{config['priority']}] {config['display_name']}")
                
            except Exception as e:
                if self.log_attempts:
                    logger.warning(f"     ⚠️  전략 로드 실패 ({name}): {e}")
    
    def __init__(self, driver, log_attempts=True, custom_strategies=None, order=None):
        """
        초기화
        
        Args:
            driver: Selenium WebDriver
            log_attempts: bool - 로그 출력 여부
            custom_strategies: dict - 커스텀 전략 설정 (선택)
            order: list - 사용할 전략 이름 목록 (순서대로 시도, optional)
                   예: ["browser", "cdp_print"]
                   None이면 기본값 사용 (network, browser, cdp_print)
        """
        self.driver = driver
        self.log_attempts = log_attempts
        
        # ⭐ order 처리
        if order:
            # 사용자가 선택한 전략만 활성화
            strategies_config = self.override_strategies(order=order)
            if log_attempts:
                logger.info(f"  🎯 PDF Retrieval Controller 초기화 (선택된 전략: {order})")
        elif custom_strategies:
            # 커스텀 전략 설정 사용
            strategies_config = custom_strategies
            if log_attempts:
                logger.info(f"  🎯 PDF Retrieval Controller 초기화 (커스텀)")
        else:
            # ⭐ 기본값: network, browser, cdp_print 활성화
            default_order = ["network", "browser", "cdp_print"]
            strategies_config = self.override_strategies(order=default_order)
            if log_attempts:
                logger.info(f"  🎯 PDF Retrieval Controller 초기화 (기본 설정)")
        
        # 전략 로드
        self.__init_strategies(strategies_config)
        
        if log_attempts:
            logger.info(f"     - 활성 전략: {len(self.active_strategies)}개")
    
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
        
        # ⭐ 활성 전략 순서대로 시도
        for idx, strategy_name in enumerate(self.active_strategies, 1):
            strategy_info = self.strategy_registry[strategy_name]
            strategy = strategy_info["instance"]
            config = strategy_info["config"]
            
            if self.log_attempts:
                logger.info(f"  📌 [{idx}/{len(self.active_strategies)}] {config['display_name']} 시도...")
            
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
                        logger.info(f"  ✅ {config['display_name']} 성공: {result}")
                    return result
                
                if self.log_attempts:
                    logger.warning(f"  ⚠️  {config['display_name']} 실패 - 다음 전략 시도")
            
            except Exception as e:
                if self.log_attempts:
                    logger.error(f"  ❌ {config['display_name']} 오류: {e}")
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
