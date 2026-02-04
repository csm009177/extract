"""
KR-CON 로그인 모듈
- download_all.py, inspect_page.py에서 공통으로 사용
"""
import logging
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

def login_to_krcon(driver, wait_time=5):
    """
    KR-CON 사이트 로그인
    
    Args:
        driver: Selenium WebDriver 인스턴스
        wait_time: 로그인 후 대기 시간 (초)
    
    Returns:
        bool: 로그인 성공 여부
    """
    logger.info("🔐 로그인 중...")
    
    # 환경 변수에서 로그인 정보 가져오기
    user_id = os.getenv("KRCON_USER_ID")
    password = os.getenv("KRCON_PASSWORD")
    
    if not user_id or not password:
        logger.error("❌ 로그인 정보가 .env 파일에 설정되지 않았습니다!")
        logger.error("   KRCON_USER_ID와 KRCON_PASSWORD를 설정하세요.")
        return False
    
    try:
        # TreeView 페이지로 바로 접근 (로그인 필요 → 로그인창 자동 표시)
        driver.get('https://krcon.krs.co.kr/Functions/TreeView/List.aspx?LocaleKey=en&Tree=0000.00e0')
        time.sleep(3)
        
        # 로그인 필드 찾기
        try:
            user_input = driver.find_element(By.ID, "ctl00_BodyContentPlaceHolder_txtId")
            pwd_input = driver.find_element(By.ID, "ctl00_BodyContentPlaceHolder_txtPwd")
            login_btn = driver.find_element(By.ID, "ctl00_BodyContentPlaceHolder_btnLogin")
            
            # 로그인 정보 입력
            user_input.clear()
            user_input.send_keys(user_id)
            
            pwd_input.clear()
            pwd_input.send_keys(password)
            
            # 로그인 버튼 클릭
            login_btn.click()
            
            # 로그인 완료 대기
            time.sleep(wait_time)
            
            # 팝업 닫기
            if len(driver.window_handles) > 1:
                for handle in driver.window_handles[1:]:
                    driver.switch_to.window(handle)
                    driver.close()
                driver.switch_to.window(driver.window_handles[0])
            
            logger.info("✅ 로그인 완료")
            return True
            
        except Exception as e:
            # 로그인 필드가 없으면 이미 로그인된 상태일 수 있음
            logger.info("ℹ️  로그인 필드를 찾을 수 없습니다. 이미 로그인된 상태일 수 있습니다.")
            
            # 현재 URL 확인
            current_url = driver.current_url
            if "krcon.krs.co.kr" in current_url:
                logger.info("✅ 로그인 상태 확인됨")
                return True
            else:
                logger.error(f"❌ 예상치 못한 페이지: {current_url}")
                return False
                
    except Exception as e:
        logger.error(f"❌ 로그인 실패: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False

def ensure_logged_in(driver):
    """
    로그인 상태 확인 및 필요시 재로그인
    
    Args:
        driver: Selenium WebDriver 인스턴스
    
    Returns:
        bool: 로그인 성공 여부
    """
    try:
        current_url = driver.current_url
        
        # 이미 로그인된 상태인지 확인
        if "krcon.krs.co.kr" in current_url and "Login" not in current_url:
            logger.debug("✓ 이미 로그인 상태")
            return True
        
        # 로그인 필요
        return login_to_krcon(driver)
        
    except Exception as e:
        logger.warning(f"⚠️  로그인 상태 확인 실패: {e}")
        return login_to_krcon(driver)
