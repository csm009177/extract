#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Retrieval Strategy: CDP
- Chrome DevTools Protocol을 사용한 PDF 회수
- 스크롤 스크린샷 방식으로 전체 페이지 캡처
"""

import os
import base64
import time
import logging
from PIL import Image
from io import BytesIO
from selenium.webdriver.common.by import By
from .button_strategies import BUTTON_STRATEGY_REGISTRY, BUTTON_STRATEGY_ORDER

logger = logging.getLogger(__name__)


class RetrievalCDP:
    """스크롤 스크린샷 방식으로 전체 페이지 PDF 생성"""
    
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
    
    def _is_scrollable(self, driver):
        """스크롤이 필요한 페이지인지 확인"""
        try:
            total_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")
            return total_height > viewport_height
        except:
            return False
    
    def _calculate_scroll_positions(self, driver, overlap=100):
        """
        스크롤 위치 목록 계산
        
        Args:
            driver: WebDriver
            overlap: 중복 영역 (px) - 이어붙임 자연스럽게
        
        Returns:
            list: 스크롤 위치 목록
        """
        try:
            total_height = driver.execute_script(
                "return Math.max("
                "  document.body.scrollHeight,"
                "  document.documentElement.scrollHeight"
                ")"
            )
            
            viewport_height = driver.execute_script("return window.innerHeight")
            
            positions = []
            current = 0
            
            while current < total_height:
                positions.append(current)
                current += (viewport_height - overlap)
            
            return positions
        except Exception as e:
            logger.error(f"      스크롤 위치 계산 실패: {e}")
            return [0]
    
    def _capture_screenshots(self, driver, positions, wait_time=1.0):
        """
        각 스크롤 위치에서 스크린샷 캡처
        
        Args:
            driver: WebDriver
            positions: 스크롤 위치 목록
            wait_time: 각 스크롤 후 대기 시간 (lazy load 대응)
        
        Returns:
            list: PNG 데이터 목록
        """
        screenshots = []
        
        for i, pos in enumerate(positions):
            try:
                logger.info(f"      ├─ 스크린샷 {i+1}/{len(positions)} (위치: {pos}px)")
                
                # 1. 스크롤
                driver.execute_script(f"window.scrollTo(0, {pos})")
                
                # 2. 렌더링 대기
                time.sleep(wait_time)
                
                # 3. Lazy load 이미지 강제 로드
                try:
                    driver.execute_script("""
                        document.querySelectorAll('img[loading="lazy"]').forEach(img => {
                            img.loading = 'eager';
                        });
                    """)
                    time.sleep(0.3)
                except:
                    pass
                
                # 4. 스크린샷
                png_data = driver.get_screenshot_as_png()
                screenshots.append(png_data)
                
            except Exception as e:
                logger.error(f"      ├─ 스크린샷 {i+1} 실패: {e}")
                continue
        
        return screenshots
    
    def _merge_screenshots_to_pdf(self, screenshots, output_path, overlap=100):
        """
        스크린샷들을 하나의 PDF로 병합
        
        Args:
            screenshots: PNG 데이터 목록
            output_path: 출력 파일 경로
            overlap: 중복 제거할 영역 (px)
        
        Returns:
            str: 저장된 파일 경로 (성공 시)
            None: 실패 시
        """
        try:
            if not screenshots:
                return None
            
            # 1. PNG → PIL Image
            images = [Image.open(BytesIO(png)) for png in screenshots]
            
            # 2. 전체 높이 계산 (중복 제거)
            width = images[0].width
            total_height = sum(img.height for img in images)
            if len(images) > 1:
                total_height -= overlap * (len(images) - 1)
            
            # 3. 빈 캔버스 생성
            merged = Image.new('RGB', (width, total_height), 'white')
            
            # 4. 이미지 이어붙이기
            y_offset = 0
            for i, img in enumerate(images):
                # 첫 이미지는 그대로, 나머지는 overlap만큼 위로
                if i > 0:
                    y_offset -= overlap
                
                merged.paste(img, (0, y_offset))
                y_offset += img.height
            
            # 5. PDF로 저장
            merged.save(output_path, 'PDF', resolution=100.0, quality=95)
            
            return output_path
            
        except Exception as e:
            logger.error(f"      └─ PDF 병합 실패: {e}")
            return None
    
    def _save_full_page_pdf(self, driver, output_path, log_attempts=False):
        """
        전체 페이지를 스크롤하며 완전한 PDF 생성
        
        Args:
            driver: WebDriver
            output_path: 출력 파일 경로
            log_attempts: 로그 출력 여부
        
        Returns:
            str: 저장된 파일 경로 (성공 시)
            None: 실패 시
        """
        try:
            if log_attempts:
                logger.info("      ├─ 전체 페이지 PDF 생성 시작...")
            
            # 1. 스크롤 필요 여부 확인
            if not self._is_scrollable(driver):
                if log_attempts:
                    logger.info("      ├─ 스크롤 불필요 - 단일 스크린샷")
                
                png = driver.get_screenshot_as_png()
                img = Image.open(BytesIO(png))
                img.save(output_path, 'PDF', resolution=100.0, quality=95)
                return output_path
            
            # 2. 스크롤 위치 계산
            positions = self._calculate_scroll_positions(driver, overlap=100)
            if log_attempts:
                logger.info(f"      ├─ 총 {len(positions)}개 구간 캡처 예정")
            
            # 3. 스크린샷 캡처
            screenshots = self._capture_screenshots(driver, positions, wait_time=0.8)
            
            if not screenshots:
                if log_attempts:
                    logger.error("      └─ 스크린샷 캡처 실패")
                return None
            
            # 4. PDF 병합
            result = self._merge_screenshots_to_pdf(screenshots, output_path, overlap=100)
            
            if result and log_attempts:
                file_size = os.path.getsize(result)
                logger.info(f"      └─ PDF 생성 완료: {file_size:,} bytes")
            
            return result
            
        except Exception as e:
            if log_attempts:
                logger.error(f"      └─ PDF 생성 실패: {e}")
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
            
            # 2. 현재 URL 저장 (새 창이 아니라 URL 변경 감지)
            original_window = driver.current_window_handle
            original_url = driver.current_url
            
            # 3. 버튼 클릭
            button.click()
            
            if log_attempts:
                logger.info(f"      ├─ 버튼 클릭: 완료")
            
            # 4. URL 변경 대기 (새 창이 아니라 location.href 방식)
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            try:
                # IsPrint=true 파라미터가 추가된 페이지로 이동 대기 (최대 10초)
                WebDriverWait(driver, 10).until(
                    lambda d: "IsPrint=true" in d.current_url or d.current_url != original_url
                )
                time.sleep(2)  # 페이지 로딩 완료 대기
                
                if log_attempts:
                    logger.info(f"      ├─ PDF 페이지 로딩: 완료 (URL 변경됨)")
            except:
                # URL이 변경되지 않았다면 그대로 진행
                time.sleep(2)
                if log_attempts:
                    logger.warning(f"      ├─ URL 변경 없음 (그대로 진행)")
            
            # 4.5 ⭐ PDF 창 디버깅 정보 수집
            if log_attempts:
                logger.info("      " + "=" * 50)
                logger.info("      🔍 PDF 창 디버깅 정보")
                logger.info("      " + "=" * 50)
                logger.info(f"      📍 현재 URL: {driver.current_url}")
                logger.info(f"      � 원본 URL: {original_url}")
                logger.info(f"      �📄 Title: {driver.title}")
                
                try:
                    content_type = driver.execute_script("return document.contentType")
                    logger.info(f"      📦 Content-Type: {content_type}")
                except:
                    logger.info(f"      📦 Content-Type: (확인 불가)")
                
                # IsPrint 파라미터 확인
                is_print_mode = "IsPrint=true" in driver.current_url
                logger.info(f"      🖨️  IsPrint 모드: {is_print_mode}")
                
                # iframe 확인 (PDF가 iframe 안에 있을 수 있음)
                try:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    logger.info(f"      🖼️  iframe 개수: {len(iframes)}")
                    if iframes:
                        for i, iframe in enumerate(iframes[:5]):  # 최대 5개
                            try:
                                iframe_id = iframe.get_attribute("id")
                                src = iframe.get_attribute("src")
                                display = iframe.get_attribute("style")
                                logger.info(f"         └─ iframe[{i}] id='{iframe_id}', display='{display[:30] if display else 'None'}'")
                                if src:
                                    logger.info(f"            src: {src[:100]}...")
                            except:
                                pass
                except Exception as e:
                    logger.info(f"      🖼️  iframe 확인 실패: {e}")
                
                # embed/object 태그 확인
                try:
                    embeds = driver.find_elements(By.TAG_NAME, "embed")
                    objects = driver.find_elements(By.TAG_NAME, "object")
                    logger.info(f"      📎 embed 태그: {len(embeds)}, object 태그: {len(objects)}")
                    if embeds:
                        for i, embed in enumerate(embeds[:3]):
                            try:
                                src = embed.get_attribute("src")
                                etype = embed.get_attribute("type")
                                logger.info(f"         └─ embed[{i}] type={etype}, src={src[:80] if src else 'None'}...")
                            except:
                                pass
                except Exception as e:
                    logger.info(f"      📎 embed/object 확인 실패: {e}")
                
                # JavaScript로 PDF URL 찾기 시도
                try:
                    pdf_links = driver.execute_script("""
                        var links = [];
                        // 모든 링크 중 .pdf로 끝나는 것
                        document.querySelectorAll('a[href*=".pdf"]').forEach(function(a) {
                            links.push(a.href);
                        });
                        // iframe의 src 중 PDF 관련
                        document.querySelectorAll('iframe').forEach(function(iframe) {
                            if (iframe.src && (iframe.src.includes('.pdf') || iframe.src.includes('PDF'))) {
                                links.push(iframe.src);
                            }
                        });
                        return links;
                    """)
                    if pdf_links:
                        logger.info(f"      🔗 PDF 링크 발견: {len(pdf_links)}개")
                        for i, link in enumerate(pdf_links[:3]):
                            logger.info(f"         └─ [{i}] {link[:100]}...")
                    else:
                        logger.info(f"      🔗 PDF 직접 링크: 없음")
                except Exception as e:
                    logger.info(f"      🔗 PDF 링크 검색 실패: {e}")
                
                # 페이지 소스 저장
                try:
                    if is_print_mode:
                        debug_path = "debug_output/pdf_window_isprint.html"
                    else:
                        debug_path = "debug_output/pdf_window_normal.html"
                    os.makedirs("debug_output", exist_ok=True)
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    logger.info(f"      💾 페이지 소스 저장: {debug_path}")
                except Exception as e:
                    logger.warning(f"      💾 페이지 소스 저장 실패: {e}")
                
                logger.info("      " + "=" * 50)
            
            # 5. ⭐ 스크롤 스크린샷 방식으로 전체 페이지 PDF 생성
            try:
                os.makedirs(folder_path, exist_ok=True)
                pdf_path = os.path.join(folder_path, filename)
                
                result = self._save_full_page_pdf(driver, pdf_path, log_attempts)
                
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
                        pass
                
                return result
            
            except Exception as e:
                if log_attempts:
                    logger.error(f"      └─ CDP 저장 실패: {e}")
                
                # 정리 - 오류 발생 시에도 원본 페이지로 복귀
                if driver.current_url != original_url:
                    try:
                        driver.back()
                        time.sleep(1)
                    except:
                        pass
                
                return None
        
        except Exception as e:
            if log_attempts:
                logger.error(f"      └─ 오류: {e}")
            
            # 🆕 예외 발생 시에도 원본 창으로 복귀 시도
            try:
                driver.switch_to.window(original_window)
            except:
                pass
            
            return None
