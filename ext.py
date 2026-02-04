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
from urllib.parse import urljoin
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
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

def login_to_treeview(driver, user_id, password):
    """Tree View로 직접 이동하여 로그인"""
    logger.info("🔐 Tree View 페이지로 이동...")
    
    try:
        # Tree View 페이지로 바로 이동
        driver.get('https://krcon.krs.co.kr/Functions/TreeView/Left.aspx?LocaleKey=en')
        time.sleep(3)
        
        # 현재 URL 확인
        current_url = driver.current_url
        logger.info(f"현재 URL: {current_url}")
        
        # 페이지 소스 저장 (디버그용)
        with open("treeview_debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("페이지 소스 저장: treeview_debug.html")
        
        # 로그인 필드 확인
        wait = WebDriverWait(driver, 10)
        
        # 여러 가능한 로그인 필드 ID 시도
        login_field_ids = [
            ("txtLoginUser", "txtLoginiPassword"),
            ("txtUserId", "txtPassword"),
            ("userId", "password"),
            ("username", "password")
        ]
        
        user_input = None
        password_input = None
        
        for user_id_field, pwd_field in login_field_ids:
            try:
                logger.info(f"로그인 필드 찾기 시도: {user_id_field}, {pwd_field}")
                user_input = driver.find_element(By.ID, user_id_field)
                password_input = driver.find_element(By.ID, pwd_field)
                logger.info(f"✓ 로그인 필드 발견: {user_id_field}, {pwd_field}")
                break
            except NoSuchElementException:
                continue
        
        if user_input and password_input:
            logger.info(f"✏️  아이디 입력: {user_id}")
            user_input.clear()
            user_input.send_keys(user_id)
            
            logger.info("✏️  비밀번호 입력")
            password_input.clear()
            password_input.send_keys(password)
            
            # JavaScript로 로그인 함수 호출
            logger.info("🔘 로그인 실행...")
            driver.execute_script("proccessLogin();")
            
            # 로그인 완료 대기
            time.sleep(5)
            
            logger.info("✅ 로그인 완료!")
            return True
        else:
            logger.warning("⚠️  로그인 필드를 찾을 수 없습니다. 이미 로그인된 상태일 수 있습니다.")
            return True
            
    except Exception as e:
        logger.error(f"❌ 로그인 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# ===== Selenium 기반 크롤링 =====
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("KR-CON 크롤러 시작 (Selenium)")
    logger.info("=" * 50)
    
    # Chrome 드라이버 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = None
    try:
        logger.info("Chrome 브라우저 시작...")
        driver = webdriver.Chrome(options=options)
        
        # 환경 변수에서 로그인 정보 가져오기
        user_id = os.getenv("KRCON_USER_ID")
        password = os.getenv("KRCON_PASSWORD")
        
        if not user_id or not password:
            logger.error("로그인 정보가 환경 변수에 설정되지 않았습니다!")
            logger.error(".env 파일에 KRCON_USER_ID와 KRCON_PASSWORD를 설정하세요.")
            exit(1)
        
        # Tree View 페이지로 직접 이동하여 로그인
        if not login_to_treeview(driver, user_id, password):
            logger.error("로그인에 실패했습니다. 프로그램을 종료합니다.")
            exit(1)
        
        # 트리 요소 대기
        logger.info("🌳 트리 구조 대기...")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "rtUL"))
            )
            logger.info("✓ 트리 요소 발견!")
        except TimeoutException:
            logger.warning("⚠️  트리가 로드되지 않았을 수 있습니다. 계속 진행...")
        
        # 트리 전체 확장 (재귀적으로 모든 하위 노드 확장)
        logger.info("🌲 트리 전체 확장 중 (재귀적)...")
        try:
            max_iterations = 10  # 최대 반복 횟수
            total_expanded = 0
            
            for iteration in range(max_iterations):
                # 현재 확장 가능한 모든 + 버튼 찾기
                expand_buttons = driver.find_elements(By.CSS_SELECTOR, "span.rtPlus")
                
                if len(expand_buttons) == 0:
                    logger.info(f"✓ 더 이상 확장할 노드가 없습니다 (반복 {iteration + 1}회)")
                    break
                
                logger.info(f"  [{iteration + 1}회] 확장 가능한 노드 {len(expand_buttons)}개 발견")
                
                # 모든 노드 확장
                for i, button in enumerate(expand_buttons):
                    try:
                        driver.execute_script("arguments[0].click();", button)
                        total_expanded += 1
                        time.sleep(0.05)  # 짧은 대기
                    except:
                        pass
                
                # 새로운 노드가 로드될 때까지 대기
                time.sleep(1)
            
            logger.info(f"✓ 트리 확장 완료! (총 {total_expanded}개 노드 확장)")
            time.sleep(2)  # 모든 노드가 완전히 로드될 때까지 대기
            
        except Exception as e:
            logger.warning(f"트리 확장 중 오류: {e}")
        
        # 페이지 소스 저장
        page_source = driver.page_source
        
        with open("tree_debug.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        logger.info(f"✓ 페이지 저장됨: tree_debug.html ({len(page_source)} bytes)")
        
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(page_source, 'html.parser')
        
        root_ul = soup.find("ul", class_="rtUL")
        all_nodes = []
        
        if root_ul:
            logger.info("✓ 트리 구조 발견!")
            for li in root_ul.find_all("li", recursive=False):
                all_nodes += parse_tree(li)
        else:
            logger.warning("⚠️  트리 구조를 찾을 수 없습니다!")
        
        logger.info(f"📊 총 {len(all_nodes)}개 노드 발견")
        
        if len(all_nodes) > 0:
            logger.info("\n발견된 노드 목록:")
            for node in all_nodes[:10]:  # 처음 10개만 표시
                logger.info(f"  - {node['name']} (ID: {node['id']})")
            if len(all_nodes) > 10:
                logger.info(f"  ... 외 {len(all_nodes) - 10}개")
            
            # JSON 파일로 저장
            logger.info("\n💾 트리 구조를 JSON으로 저장 중...")
            tree_data = {
                "total_nodes": len(all_nodes),
                "crawled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "nodes": all_nodes
            }
            
            with open("tree_structure.json", "w", encoding="utf-8") as f:
                json.dump(tree_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 저장 완료: tree_structure.json")
            logger.info(f"   📁 총 {len(all_nodes)}개 노드")
            
            # 통계 정보
            depth_count = {}
            for node in all_nodes:
                depth = node['path'].count('/')
                depth_count[depth] = depth_count.get(depth, 0) + 1
            
            logger.info("\n📊 트리 깊이 통계:")
            for depth in sorted(depth_count.keys()):
                logger.info(f"   Level {depth}: {depth_count[depth]}개")
        
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
