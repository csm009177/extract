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
    
    def download(self, folder_path, filename, node_name="Unknown"):
        """
        PDF 다운로드 (3가지 retrieval 방식 순차 시도)
        
        Args:
            folder_path: 저장 폴더 경로
            filename: 파일명
            node_name: 노드 이름 (로그용)
        
        Returns:
            str: 저장된 파일 경로 또는 None
        """
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
