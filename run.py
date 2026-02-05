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
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
from dotenv import load_dotenv

# 모듈 import
from modules.auth import login_to_krcon, ensure_logged_in
from modules.tree_collector import collect_tree_structure
from modules.pdf_detectors import download_pdf

# 환경 변수 로드
load_dotenv()

# 로깅 설정
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'download.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 설정
BASE_DIR = "output/downloads"
TREE_FILE = "output/tree_structure.json"
PROGRESS_FILE = "output/download_progress.json"

MAX_REQUESTS_PER_MINUTE = 10
DELAY_RANGE = (3, 7)
MAX_RETRIES = 3
PAGE_LOAD_TIMEOUT = 30

request_times = []

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

def load_progress():
    """진행 상황 로드"""
    if not os.path.exists(PROGRESS_FILE):
        return 0
    
    if not os.path.exists(BASE_DIR):
        logger.warning("⚠️  downloads 폴더가 비어있습니다. 처음부터 시작합니다.")
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
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "last_processed_index": index,
                "saved_at": datetime.now().isoformat()
            }, f, indent=2)
        logger.info(f"💾 진행 상황 저장: {index}/{total}")
    except Exception as e:
        logger.error(f"진행 상황 저장 실패: {e}")

def check_and_relogin(driver):
    """세션 확인 및 필요시 재로그인 (세션 만료 대비)"""
    try:
        current_url = driver.current_url
        
        # 로그인 페이지로 리다이렉트되었는지 확인
        if "login" in current_url.lower() or "logon" in current_url.lower():
            logger.warning(f"⚠️  세션 만료 감지 - 재로그인 시도")
            
            from modules.auth import login_to_krcon
            if login_to_krcon(driver):
                logger.info(f"✅ 재로그인 성공")
                return True
            else:
                logger.error(f"❌ 재로그인 실패")
                return False
        
        return True  # 세션 정상
    
    except Exception as e:
        logger.warning(f"⚠️  세션 확인 중 오류: {e}")
        return True  # 오류 시 일단 통과


def download_pdf_files(driver, node, folder_path):
    """
    PDF 파일 다운로드 (Retrieval 아키텍처)
    
    download_pdf()가 자동으로 처리:
        [1/3] retrieval_cdp 시도...
              ├─ 버튼 찾기: 성공 (내부 자동)
              ├─ 버튼 클릭: 완료
              └─ CDP 저장: 성공 ✅
    """
    node_name = node.get('name', 'Unknown')
    
    try:
        # ===== PDF 다운로드 (3가지 retrieval 방식 자동 시도) =====
        filename = safe_name(node_name) + '.pdf'
        pdf_path = download_pdf(
            driver=driver,
            folder_path=folder_path,
            filename=filename,
            node_name=node_name,
            log_attempts=True
        )
        
        if pdf_path:
            return 1
        else:
            return 0
        
    except Exception as e:
        logger.error(f"  ❌ PDF 다운로드 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0

def download_node(driver, node, retry_count=0):
    """개별 노드 다운로드 - (성공여부, PDF개수) 튜플 반환"""
    node_name = node.get('name', 'Unknown')
    node_href = node.get('href', '')
    
    if not node_href:
        return (False, 0)
    
    try:
        rate_limit()
        
        # 세션 확인 및 재로그인 (세션 만료 대비)
        if not check_and_relogin(driver):
            logger.error(f"  ❌ 재로그인 실패: {node_name}")
            return (False, 0)
        
        folder_path = os.path.join(BASE_DIR, node.get('path', safe_name(node_name)))
        os.makedirs(folder_path, exist_ok=True)
        
        html_path = os.path.join(folder_path, safe_name(node_name) + '.html')
        
        if os.path.exists(html_path):
            logger.info(f"  ⏭️  건너뛰기: {node_name}")
            return (True, 0)  # 이미 존재하면 성공이지만 PDF는 0개
        
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
            return (False, 0)
        
        # HTML 저장
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info(f"  ✓ HTML: {safe_name(node_name)}.html")
        
        # ✅ PDF 다운로드 호출
        pdf_count = download_pdf_files(driver, node, folder_path)
        if pdf_count > 0:
            logger.info(f"  ✓ PDF {pdf_count}개 완료")
        
        random_delay()
        return (True, pdf_count)  # 성공과 PDF 개수 반환
        
    except TimeoutException:
        if retry_count < MAX_RETRIES:
            return download_node(driver, node, retry_count + 1)
        return (False, 0)
        
    except Exception as e:
        logger.error(f"  ✗ 오류: {e}")
        if retry_count < MAX_RETRIES:
            random_delay()
            return download_node(driver, node, retry_count + 1)
        return (False, 0)

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

if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("🚀 KR-CON 자동 다운로더")
    logger.info("="*70)
    
    driver = None
    success_count = 0
    fail_count = 0
    pdf_count = 0  # PDF 카운트 추가
    
    try:
        # Chrome 설정
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        logger.info("🌐 Chrome 브라우저 시작...")
        driver = webdriver.Chrome(options=options)
        
        # 로그인
        if not login_to_krcon(driver):
            logger.error("❌ 로그인 실패. 종료합니다.")
            exit(1)
        
        # 1단계: 트리 구조 확인
        logger.info("\n" + "="*70)
        logger.info("📋 1단계: 트리 구조 확인")
        logger.info("="*70)
        
        if not os.path.exists(TREE_FILE):
            logger.info(f"📋 {TREE_FILE} 없음. 트리 구조를 수집합니다...")
            nodes = collect_tree_structure(driver, TREE_FILE)
        else:
            logger.info(f"✅ {TREE_FILE} 발견. 기존 데이터를 사용합니다.")
            with open(TREE_FILE, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
                nodes = tree_data.get('nodes', [])
            logger.info(f"📊 총 {len(nodes)}개 노드 로드 완료\n")
        
        total_nodes = len(nodes)
        
        if total_nodes == 0:
            logger.error("❌ 다운로드할 노드가 없습니다!")
            exit(1)
        
        # 2단계: 진행 상황 확인
        start_index = load_progress()
        
        # 3단계: 다운로드 시작
        logger.info("="*70)
        logger.info(f"📥 2단계: 콘텐츠 다운로드 ({start_index + 1}/{total_nodes})")
        logger.info("="*70)
        logger.info(f"⚙️  설정: 지연 {DELAY_RANGE[0]}-{DELAY_RANGE[1]}초, 분당 최대 {MAX_REQUESTS_PER_MINUTE}회\n")
        
        for i in range(start_index, total_nodes):
            node = nodes[i]
            
            logger.info(f"\n[{i+1}/{total_nodes}] {node.get('name', 'Unknown')}")
            
            success, node_pdf_count = download_node(driver, node)
            if success:
                success_count += 1
                pdf_count += node_pdf_count  # PDF 개수 누적
            else:
                fail_count += 1
            
            # 10개마다 저장
            if (i + 1) % 10 == 0:
                save_progress(i + 1, total_nodes)
                logger.info(f"\n📊 중간 통계: 성공 {success_count}, 실패 {fail_count}, PDF {pdf_count}개\n")
        
        save_progress(total_nodes, total_nodes)
        
        logger.info("\n" + "="*70)
        logger.info("✅ 다운로드 완료!")
        logger.info(f"📊 최종: 성공 {success_count}, 실패 {fail_count}, PDF {pdf_count}개")
        logger.info("="*70)
        
    except KeyboardInterrupt:
        logger.info("\n" + "="*70)
        logger.info("⚠️  사용자 중단")
        logger.info("="*70)
        logger.info(f"📊 통계: 성공 {success_count}, 실패 {fail_count}, PDF {pdf_count}개")
        
        if 'i' in locals():
            save_progress(i + 1, total_nodes)
            logger.info(f"💾 진행: {i+1}/{total_nodes} ({(i+1)/total_nodes*100:.1f}%)")
        
    except Exception as e:
        logger.error(f"\n❌ 에러: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.info(f"📊 통계: 성공 {success_count}, 실패 {fail_count}, PDF {pdf_count}개")
    
    finally:
        safe_quit_driver(driver)
        logger.info("\n프로그램 종료\n")
