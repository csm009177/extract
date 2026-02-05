#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
버튼 찾기 전략 레지스트리
"""

from .by_id import IDDetector
from .by_fontawesome import FontAwesomeDetector
from .by_onclick import OnClickDetector
from .by_btn_group import BtnGroupDetector
from .by_text import TextDetector
from .by_sibling import SiblingDetector
from .by_javascript import JavaScriptDetector
from .by_css import CSSDetector

# 버튼 찾기 전략 레지스트리
BUTTON_STRATEGY_REGISTRY = {
    "id": IDDetector(),
    "fontawesome": FontAwesomeDetector(),
    "onclick": OnClickDetector(),
    "btn_group": BtnGroupDetector(),
    "text": TextDetector(),
    "sibling": SiblingDetector(),
    "javascript": JavaScriptDetector(),
    "css": CSSDetector(),
}

# 우선순위 순으로 정렬된 전략 이름 리스트
BUTTON_STRATEGY_ORDER = sorted(
    BUTTON_STRATEGY_REGISTRY.keys(),
    key=lambda name: BUTTON_STRATEGY_REGISTRY[name].PRIORITY
)

__all__ = ['BUTTON_STRATEGY_REGISTRY', 'BUTTON_STRATEGY_ORDER']
