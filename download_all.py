import logging
import os
import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 진행 상황 파일
PROGRESS_FILE = "download_progress.json"
FAILED_LOG = "failed_downloads.log"

def load_progress():
    """다운로드 진행 상황 로드"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed": [], "last_index": -1}

def save_progress(progress):
    """다운로드 진행 상황 저장"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def log_failed(node_info, error_msg):
    """실패한 다운로드 기록"""
    with open(FAILED_LOG, 'a', encoding='utf-8') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {node_info['name']} ({node_info['id']}) - {error_msg}\n")

def safe_name(name, max_length=80):
    """파일/폴더명에서 금지된 문자 제거"""
    name = name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('?', '_').replace('*', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
    return name[:max_length]

def create_folder_structure(base_path, node_path):
    """폴더 구조 생성"""
    folder_path = os.path.join(base_path, node_path)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def login_to_site(driver, user_id, password):
    """사이트 로그인"""
    logger.info("🔐 로그인 시도...")
    
    try:
        driver.get('https://krcon.krs.co.kr/Functions/TreeView/Left.aspx?LocaleKey=en')
        time.sleep(3)
        
        # 로그인 필드 찾기
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
                user_input = driver.find_element(By.ID, user_id_field)
                password_input = driver.find_element(By.ID, pwd_field)
                logger.info(f"✓ 로그인 필드 발견: {user_id_field}")
                break
            except NoSuchElementException:
                continue
        
        if user_input and password_input:
            user_input.clear()
            user_input.send_keys(user_id)
            password_input.clear()
            password_input.send_keys(password)
            driver.execute_script("proccessLogin();")
            time.sleep(5)
            logger.info("✅ 로그인 완료!")
            return True
        else:
            logger.warning("⚠️  로그인 필드를 찾을 수 없습니다. 이미 로그인된 상태일 수 있습니다.")
            return True
            
    except Exception as e:
        logger.error(f"❌ 로그인 실패: {str(e)}")
        return False

def download_content(driver, node, base_path):
    """개별 노드의 콘텐츠 다운로드"""
    try:
        # 폴더 생성
        folder_path = create_folder_structure(base_path, node['path'])
        
        # URL 구성
        if node['href']:
            full_url = f"https://krcon.krs.co.kr/Functions/TreeView/{node['href']}"
            
            logger.info(f"📥 다운로드 시도: {node['name']}")
            
            # 페이지 방문
            driver.get(full_url)
            time.sleep(2)
            
            # 페이지 소스 저장 (임시)
            # TODO: 실제 다운로드 로직 구현 필요
            # - PDF 링크 찾기
            # - 파일 다운로드
            # - 메타데이터 저장 등
            
            page_source = driver.page_source
            html_file = os.path.join(folder_path, f"{safe_name(node['name'])}.html")
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            logger.info(f"✓ 저장 완료: {html_file}")
            return True
        else:
            logger.warning(f"⚠️  href 없음: {node['name']}")
            return False
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ 다운로드 실패: {node['name']} - {error_msg}")
        log_failed(node, error_msg)
        return False

def main():
    logger.info("=" * 50)
    logger.info("KR-CON 다운로드 크롤러 시작")
    logger.info("=" * 50)
    
    # tree_structure.json 로드
    if not os.path.exists("tree_structure.json"):
        logger.error("❌ tree_structure.json 파일을 찾을 수 없습니다!")
        logger.error("먼저 ext.py를 실행하여 트리 구조를 수집하세요.")
        return
    
    with open("tree_structure.json", 'r', encoding='utf-8') as f:
        tree_data = json.load(f)
    
    nodes = tree_data['nodes']
    total_nodes = len(nodes)
    logger.info(f"📊 총 {total_nodes}개 노드 발견")
    
    # 진행 상황 로드
    progress = load_progress()
    start_index = progress['last_index'] + 1
    
    if start_index > 0:
        logger.info(f"🔄 이전 진행 상황 발견! {start_index}번째부터 재개합니다.")
    
    # Chrome 드라이버 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # 다운로드 설정
    download_path = os.path.abspath("downloads")
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    
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
            return
        
        # 로그인
        if not login_to_site(driver, user_id, password):
            logger.error("로그인에 실패했습니다. 프로그램을 종료합니다.")
            return
        
        # 다운로드 시작
        logger.info(f"\n📥 다운로드 시작 ({start_index + 1}/{total_nodes})...\n")
        
        success_count = 0
        failed_count = 0
        
        for i in range(start_index, total_nodes):
            node = nodes[i]
            
            logger.info(f"[{i + 1}/{total_nodes}] {node['name']}")
            
            if download_content(driver, node, "downloads"):
                success_count += 1
            else:
                failed_count += 1
            
            # 진행 상황 저장 (10개마다)
            if (i + 1) % 10 == 0:
                progress['last_index'] = i
                progress['completed'].append(node['id'])
                save_progress(progress)
                logger.info(f"💾 진행 상황 저장됨 ({i + 1}/{total_nodes})")
            
            # 요청 간격 (서버 부하 방지)
            time.sleep(1)
        
        # 최종 진행 상황 저장
        progress['last_index'] = total_nodes - 1
        save_progress(progress)
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ 다운로드 완료!")
        logger.info(f"   성공: {success_count}개")
        logger.info(f"   실패: {failed_count}개")
        logger.info("=" * 50)
        
        if failed_count > 0:
            logger.info(f"⚠️  실패한 항목은 {FAILED_LOG}에서 확인하세요.")
        
    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 중단되었습니다")
        logger.info(f"진행 상황이 저장되었습니다. 다시 실행하면 이어서 진행됩니다.")
    except Exception as e:
        logger.error(f"❌ 에러 발생: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        if driver:
            logger.info("🔚 브라우저 종료...")
            driver.quit()

if __name__ == "__main__":
    main()
