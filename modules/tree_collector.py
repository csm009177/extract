"""
트리 구조 수집 모듈
- KR-CON 사이트의 트리 구조를 수집하여 JSON으로 저장
"""

import logging
import os
import time
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from .auth import login_to_krcon

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def safe_name(name, max_length=80):
    """파일/폴더명에서 금지된 문자 제거"""
    name = name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('?', '_').replace('*', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
    return name[:max_length]

def parse_tree(li, parent_path=""):
    """재귀적으로 트리 구조 파싱"""
    nodes = []
    
    # <div class="rtTop|rtMid|rtBot"> 안의 <a> 태그 찾기
    div_container = li.find("div", class_=["rtTop", "rtMid", "rtBot"], recursive=False)
    if not div_container:
        return nodes
    
    a_tag = div_container.find("a", class_="rtIn")
    if not a_tag:
        return nodes
    
    node_name = a_tag.get_text(strip=True)
    
    # href에서 Tree ID 추출 (예: List.aspx?LocaleKey=en&Tree=0000.00e0)
    import re
    href = a_tag.get("href", "")
    match = re.search(r"Tree=([^&]+)", href)
    node_id = match.group(1) if match else None
    
    # 현재 경로 생성
    current_path = f"{parent_path}/{safe_name(node_name)}" if parent_path else safe_name(node_name)
    
    # 현재 노드 추가
    nodes.append({
        "name": node_name,
        "id": node_id,
        "path": current_path,
        "href": href
    })
    
    # 자식 노드 재귀 파싱
    ul_tag = li.find("ul", class_="rtUL", recursive=False)
    if ul_tag:
        for child_li in ul_tag.find_all("li", class_="rtLI", recursive=False):
            nodes += parse_tree(child_li, current_path)
    
    return nodes

def collect_tree_structure(driver, output_file="output/tree_structure.json"):
    """
    트리 구조 수집 (모듈로 사용 가능)
    
    Args:
        driver: Selenium WebDriver 인스턴스 (이미 로그인된 상태)
        output_file: 저장할 JSON 파일명
    
    Returns:
        list: 수집된 노드 목록
    """
    logger.info("\n" + "="*50)
    logger.info("🌳 트리 구조 수집 시작")
    logger.info("="*50)
    
    try:
        # TreeView Left 페이지로 이동
        logger.info("트리 페이지 접속...")
        driver.get('https://krcon.krs.co.kr/Functions/TreeView/Left.aspx?LocaleKey=en')
        time.sleep(3)
        
        # 트리 요소 대기
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "rtUL"))
            )
            logger.info("✓ 트리 요소 발견")
        except TimeoutException:
            logger.warning("⚠️  트리 로드 지연")
        
        # 트리 전체 확장
        logger.info("🌲 트리 확장 중...")
        max_iterations = 10
        total_expanded = 0
        
        for iteration in range(max_iterations):
            expand_buttons = driver.find_elements(By.CSS_SELECTOR, "span.rtPlus")
            
            if len(expand_buttons) == 0:
                logger.info(f"✓ 확장 완료 ({iteration + 1}회 반복)")
                break
            
            logger.info(f"  [{iteration + 1}회] {len(expand_buttons)}개 노드 확장 중...")
            
            for button in expand_buttons:
                try:
                    driver.execute_script("arguments[0].click();", button)
                    total_expanded += 1
                    time.sleep(0.05)
                except:
                    pass
            
            time.sleep(1)
        
        logger.info(f"✓ 총 {total_expanded}개 노드 확장 완료")
        time.sleep(2)
        
        # 파싱
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        root_ul = soup.find("ul", class_="rtUL")
        
        all_nodes = []
        if root_ul:
            logger.info("✓ 트리 구조 발견!")
            for li in root_ul.find_all("li", recursive=False):
                all_nodes += parse_tree(li)
        else:
            logger.warning("⚠️  트리 구조를 찾을 수 없습니다!")
            return []
        
        logger.info(f"📊 총 {len(all_nodes)}개 노드 발견")
        
        # JSON 저장
        tree_data = {
            "total_nodes": len(all_nodes),
            "crawled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "nodes": all_nodes
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(tree_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 저장 완료: {output_file}")
        
        # 통계
        depth_count = {}
        for node in all_nodes:
            depth = node['path'].count('/')
            depth_count[depth] = depth_count.get(depth, 0) + 1
        
        logger.info("\n📊 트리 깊이 통계:")
        for depth in sorted(depth_count.keys()):
            logger.info(f"   Level {depth}: {depth_count[depth]}개")
        
        return all_nodes
        
    except Exception as e:
        logger.error(f"❌ 트리 수집 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

# ===== 독립 실행 모드 =====
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("KR-CON 트리 수집기 (독립 실행)")
    logger.info("=" * 50)
    
    # Chrome 드라이버 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = None
    try:
        logger.info("Chrome 브라우저 시작...")
        driver = webdriver.Chrome(options=options)
        
        # 로그인
        if not login_to_krcon(driver):
            logger.error("로그인에 실패했습니다. 프로그램을 종료합니다.")
            exit(1)
        
        # 트리 구조 수집
        nodes = collect_tree_structure(driver)
        
        if len(nodes) > 0:
            logger.info("\n발견된 노드 목록 (처음 10개):")
            for node in nodes[:10]:
                logger.info(f"  - {node['name']} (ID: {node['id']})")
            if len(nodes) > 10:
                logger.info(f"  ... 외 {len(nodes) - 10}개")
        
        # 브라우저 유지 (확인용)
        logger.info("\n브라우저를 유지합니다. 종료하려면 Enter를 누르세요...")
        input()
        
    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 중단되었습니다")
    except Exception as e:
        logger.error(f"❌ 에러 발생: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        if driver:
            logger.info("🔚 브라우저 종료...")
            driver.quit()
    
    logger.info("=" * 50)
    logger.info("크롤링 완료")
    logger.info("=" * 50)
