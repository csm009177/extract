#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KR-CON 자동 다운로더
- 단일 진입점으로 모든 작업 자동화
"""

import logging
import os
import time
import json
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from dotenv import load_dotenv

# 모듈 import
from modules import login_to_krcon, ensure_logged_in, collect_tree_structure, DownloadStatus

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/download.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== 설정 =====
BASE_DIR = "output/downloads"
TREE_FILE = "output/tree_structure.json"
PROGRESS_FILE = "output/download_progress.json"
FAILED_LOG = "logs/failed_downloads.log"

# Rate limiting 설정
MAX_REQUESTS_PER_MINUTE = 10
DELAY_RANGE = (3, 7)
MAX_RETRIES = 3
PAGE_LOAD_TIMEOUT = 30

request_times = []

# ===== 유틸리티 함수 =====
def safe_name(name, max_length=80):
    """파일/폴더명에서 금지된 문자 제거"""
    name = name.replace('/', '_').replace('\\', '_').replace(':', '_') \
               .replace('?', '_').replace('*', '_').replace('"', '_') \
               .replace('<', '_').replace('>', '_').replace('|', '_')
    return name[:max_length]

def rate_limit():
    """분당 요청 수 제한"""
    global request_times
    now = datetime.now()
    request_times = [t for t in request_times if (now - t).seconds < 60]
    
    if len(request_times) >= MAX_REQUESTS_PER_MINUTE:
        wait_time = 60 - (now - request_times[0]).seconds
        logger.info(f"⏳ Rate limit 도달. {wait_time}초 대기 중...")
        time.sleep(wait_time)
        request_times.clear()
    
    request_times.append(now)

def random_delay():
    """랜덤 지연"""
    delay = random.uniform(*DELAY_RANGE)
    time.sleep(delay)

def close_popups(driver):
    """팝업 창 닫기"""
    try:
        windows = driver.window_handles
        if len(windows) > 1:
            logger.info(f"🔔 팝업 {len(windows)-1}개 감지. 닫는 중...")
            main_window = windows[0]
            for window in windows[1:]:
                driver.switch_to.window(window)
                driver.close()
            driver.switch_to.window(main_window)
            logger.info("✓ 팝업 닫기 완료")
            return True
    except Exception as e:
        logger.debug(f"팝업 체크 오류 (무시됨): {e}")
    return False

# ===== 진행 상황 관리 =====
def load_progress():
    """진행 상황 로드"""
    if not os.path.exists(PROGRESS_FILE):
        return 0
    
    if not os.path.exists(BASE_DIR):
        logger.warning("⚠️  downloads 폴더가 없습니다. 처음부터 시작합니다.")
        try:
            os.remove(PROGRESS_FILE)
        except:
            pass
        return 0
    
    file_count = sum(len(files) for _, _, files in os.walk(BASE_DIR))
    
    if file_count == 0:
        logger.warning("⚠️  downloads 폴더가 비어있습니다. 처음부터 시작합니다.")
        try:
            os.remove(PROGRESS_FILE)
        except:
            pass
        return 0
    
    try:
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            progress = json.load(f)
            last_index = progress.get("last_processed_index", 0)
            logger.info(f"🔄 이전 진행 상황: {last_index}번째부터 재개 ({file_count}개 파일 존재)")
            return last_index
    except Exception as e:
        logger.error(f"진행 상황 로드 실패: {e}")
        return 0

def save_progress(index, total):
    """진행 상황 저장"""
    try:
        os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "last_processed_index": index,
                "saved_at": datetime.now().isoformat()
            }, f, indent=2)
        logger.info(f"💾 진행 상황 저장: {index}/{total}")
    except Exception as e:
        logger.error(f"진행 상황 저장 실패: {e}")

# ===== 다운로드 함수 =====
def download_pdf_files(driver, node, folder_path):
    """PDF 파일 다운로드"""
    pdf_count = 0
    
    try:
        pdf_selectors = [
            "a[href$='.pdf']",
            "a[href*='.pdf']",
            "a[href*='Download']",
            "a.download-link",
            "a[title*='PDF']",
        ]
        
        pdf_links = []
        for selector in pdf_selectors:
            try:
                links = driver.find_elements(By.CSS_SELECTOR, selector)
                pdf_links.extend(links)
            except:
                pass
        
        unique_links = {}
        for link in pdf_links:
            try:
                href = link.get_attribute('href')
                if href and href not in unique_links:
                    unique_links[href] = link
            except:
                pass
        
        if not unique_links:
            return 0
        
        logger.info(f"  📕 PDF {len(unique_links)}개 발견")
        
        for idx, (pdf_url, link) in enumerate(unique_links.items(), 1):
            try:
                pdf_name = link.text.strip() or f"document_{idx}"
                pdf_name = safe_name(pdf_name)
                
                if not pdf_name.endswith('.pdf'):
                    pdf_name += '.pdf'
                
                pdf_path = os.path.join(folder_path, pdf_name)
                
                if os.path.exists(pdf_path):
                    continue
                
                cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
                response = requests.get(pdf_url, cookies=cookies, timeout=30)
                response.raise_for_status()
                
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                
                pdf_count += 1
                logger.info(f"  ✓ PDF: {pdf_name}")
                
            except Exception as e:
                logger.warning(f"  ✗ PDF 실패: {e}")
        
        return pdf_count
        
    except Exception as e:
        logger.error(f"  ✗ PDF 탐색 오류: {e}")
        return 0

def download_node(driver, node, retry_count=0):
    """개별 노드 다운로드"""
    node_name = node.get('name', 'Unknown')
    node_href = node.get('href', '')
    
    if not node_href:
        return False
    
    try:
        rate_limit()
        
        folder_path = os.path.join(BASE_DIR, node.get('path', safe_name(node_name)))
        os.makedirs(folder_path, exist_ok=True)
        
        html_path = os.path.join(folder_path, safe_name(node_name) + '.html')
        
        if os.path.exists(html_path):
            logger.info(f"  ⏭️  건너뛰기: {node_name}")
            return True
        
        base_url = 'https://krcon.krs.co.kr/Functions/TreeView/'
        full_url = base_url + node_href
        
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.get(full_url)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        if not ensure_logged_in(driver):
            if retry_count < MAX_RETRIES:
                logger.info(f"  🔄 재시도 ({retry_count + 1}/{MAX_RETRIES})")
                random_delay()
                return download_node(driver, node, retry_count + 1)
            return False
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info(f"  ✓ HTML: {safe_name(node_name)}.html")
        
        pdf_count = download_pdf_files(driver, node, folder_path)
        if pdf_count > 0:
            logger.info(f"  ✓ PDF {pdf_count}개 완료")
        
        random_delay()
        return True
        
    except TimeoutException:
        if retry_count < MAX_RETRIES:
            return download_node(driver, node, retry_count + 1)
        return False
        
    except Exception as e:
        logger.error(f"  ✗ 오류: {e}")
        if retry_count < MAX_RETRIES:
            random_delay()
            return download_node(driver, node, retry_count + 1)
        return False

def safe_quit_driver(driver):
    """안전하게 드라이버 종료"""
    if driver:
        try:
            logger.info("🔚 브라우저 종료 중...")
            driver.quit()
            logger.info("✓ 종료 완료")
        except:
            try:
                driver.service.process.kill()
            except:
                pass

# ===== 메인 실행 =====
if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("🚀 KR-CON 자동 다운로더")
    logger.info("="*70)
    
    driver = None
    success_count = 0
    fail_count = 0
    
    try:
        # output 폴더 생성
        os.makedirs("output", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Chrome 설정
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        prefs = {
            "download.default_directory": os.path.abspath(BASE_DIR),
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True
        }
        options.add_experimental_option("prefs", prefs)
        
        logger.info("🌐 Chrome 브라우저 시작...")
        driver = webdriver.Chrome(options=options)
        
        # 로그인
        if not login_to_krcon(driver):
            logger.error("❌ 로그인 실패. 종료합니다.")
            exit(1)
        
        # ===== 1단계: 트리 구조 확인 =====
        logger.info("\n" + "="*70)
        logger.info("📋 1단계: 트리 구조 확인")
        logger.info("="*70)
        
        if not os.path.exists(TREE_FILE):
            logger.info(f"⚠️  {TREE_FILE} 파일이 없습니다.")
            logger.info("🔄 자동으로 트리 구조를 수집합니다...\n")
            
            nodes = collect_tree_structure(driver, TREE_FILE)
            
            if not nodes:
                logger.error("❌ 트리 수집 실패. 종료합니다.")
                exit(1)
            
            logger.info(f"\n✅ 트리 수집 완료: {len(nodes)}개 노드\n")
        else:
            logger.info(f"✅ {TREE_FILE} 발견. 기존 데이터를 사용합니다.")
        
        # ===== 2단계: 노드 데이터 로드 =====
        with open(TREE_FILE, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)
        
        nodes = tree_data.get('nodes', [])
        total_nodes = len(nodes)
        
        logger.info(f"📊 총 {total_nodes}개 노드 로드 완료\n")
        
        if total_nodes == 0:
            logger.error("❌ 다운로드할 노드가 없습니다!")
            exit(1)
        
        # ===== 3단계: 진행 상황 확인 =====
        start_index = load_progress()
        
        # ===== 4단계: 다운로드 시작 =====
        logger.info("="*70)
        logger.info(f"📥 2단계: 콘텐츠 다운로드 ({start_index + 1}/{total_nodes})")
        logger.info("="*70)
        logger.info(f"⚙️  설정: 지연 {DELAY_RANGE[0]}-{DELAY_RANGE[1]}초, 분당 최대 {MAX_REQUESTS_PER_MINUTE}회\n")
        
        for i in range(start_index, total_nodes):
            node = nodes[i]
            
            logger.info(f"\n[{i+1}/{total_nodes}] {node.get('name', 'Unknown')}")
            
            if download_node(driver, node):
                success_count += 1
            else:
                fail_count += 1
            
            # 10개마다 저장
            if (i + 1) % 10 == 0:
                save_progress(i + 1, total_nodes)
                logger.info(f"\n📊 중간 통계: 성공 {success_count}, 실패 {fail_count}\n")
        
        save_progress(total_nodes, total_nodes)
        
        logger.info("\n" + "="*70)
        logger.info("✅ 다운로드 완료!")
        logger.info(f"📊 최종: 성공 {success_count}, 실패 {fail_count}")
        logger.info("="*70)
        
    except KeyboardInterrupt:
        logger.info("\n" + "="*70)
        logger.info("⚠️  사용자 중단")
        logger.info("="*70)
        logger.info(f"📊 통계: 성공 {success_count}, 실패 {fail_count}")
        
        if 'i' in locals():
            save_progress(i + 1, total_nodes)
            logger.info(f"💾 진행: {i+1}/{total_nodes} ({(i+1)/total_nodes*100:.1f}%)")
        
    except Exception as e:
        logger.error(f"\n❌ 에러: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.info(f"📊 통계: 성공 {success_count}, 실패 {fail_count}")
    
    finally:
        safe_quit_driver(driver)
        logger.info("\n프로그램 종료\n")
