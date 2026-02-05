#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF 다운로드 전략 레지스트리
"""

from .detector_cdp import CDPDetector
from .detector_network import NetworkDetector
from .detector_download import DownloadDetector

# PDF 다운로드 전략 레지스트리
DOWNLOAD_STRATEGY_REGISTRY = {
    "cdp": CDPDetector(),
    "network": NetworkDetector(),
    "download": DownloadDetector(),
}

# 우선순위 순으로 정렬된 전략 이름 리스트
DOWNLOAD_STRATEGY_ORDER = sorted(
    DOWNLOAD_STRATEGY_REGISTRY.keys(),
    key=lambda name: DOWNLOAD_STRATEGY_REGISTRY[name].PRIORITY
)

__all__ = ['DOWNLOAD_STRATEGY_REGISTRY', 'DOWNLOAD_STRATEGY_ORDER']
