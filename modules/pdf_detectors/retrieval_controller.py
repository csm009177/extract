#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Retrieval Controller
- PDF 회수 방식 자동 판단 및 실행
- 3가지 retrieval 방식 순차 시도
"""

import logging
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
            if not self._check_session():
                if self.log_attempts:
                    logger.error(f"  ❌ 세션 만료 - 재로그인 필요")
                return None
        
        if self.log_attempts:
            logger.info(f"  🔍 PDF 다운로드 시도: {node_name}")
            logger.info(f"     - 저장 경로: {folder_path}/{filename}")
        
        # 전략 순서대로 시도
        for idx, strategy_name in enumerate(DOWNLOAD_STRATEGY_ORDER, 1):
            strategy = DOWNLOAD_STRATEGY_REGISTRY[strategy_name]
            
            if self.log_attempts:
                logger.info(f"  📌 [{idx}/{len(DOWNLOAD_STRATEGY_ORDER)}] {strategy_name} 시도...")
            
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
                        logger.info(f"  ✅ [{strategy_name}] 성공: {result}")
                    return result
                
                if self.log_attempts:
                    logger.warning(f"  ⚠️  [{strategy_name}] 실패 - 다음 전략 시도")
            
            except Exception as e:
                if self.log_attempts:
                    logger.error(f"  ❌ [{strategy_name}] 오류: {e}")
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
            
            # 로그인 페이지로 리다이렉트되었는지 확인
            if "login" in current_url.lower() or "logon" in current_url.lower():
                return False
            
            # 세션 쿠키 확인
            cookies = self.driver.get_cookies()
            session_cookie = None
            for cookie in cookies:
                if "session" in cookie['name'].lower() or "auth" in cookie['name'].lower():
                    session_cookie = cookie
                    break
            
            if not session_cookie:
                return False
            
            return True
        
        except Exception as e:
            if self.log_attempts:
                logger.warning(f"  ⚠️  세션 확인 실패: {e}")
            return True  # 확인 실패 시 일단 통과
