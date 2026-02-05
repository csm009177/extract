#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Retrieval Strategies
- 3가지 PDF 회수 전략 등록
"""

from .retrieval_cdp import RetrievalCDP
from .retrieval_network import RetrievalNetwork
from .retrieval_browser import RetrievalBrowser

# Retrieval 전략 레지스트리
RETRIEVAL_STRATEGY_REGISTRY = {
    "retrieval_cdp": RetrievalCDP(),
    "retrieval_network": RetrievalNetwork(),
    "retrieval_browser": RetrievalBrowser(),
}

# 우선순위 순서
RETRIEVAL_STRATEGY_ORDER = [
    "retrieval_cdp",       # 1순위: CDP (Blob URL, 렌더링)
    "retrieval_network",   # 2순위: Network (직접 PDF URL)
    "retrieval_browser",   # 3순위: Browser (다운로드 폴더)
]

# 하위 호환성을 위한 별칭
DOWNLOAD_STRATEGY_REGISTRY = RETRIEVAL_STRATEGY_REGISTRY
DOWNLOAD_STRATEGY_ORDER = RETRIEVAL_STRATEGY_ORDER

__all__ = [
    'RETRIEVAL_STRATEGY_REGISTRY',
    'RETRIEVAL_STRATEGY_ORDER',
    'DOWNLOAD_STRATEGY_REGISTRY',
    'DOWNLOAD_STRATEGY_ORDER',
]
