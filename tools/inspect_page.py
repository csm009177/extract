"""KR-CON 페이지 구조 분석 도구 - PDF 다운로드 방법 파악"""

import sys
import os

# 상위 폴더를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 로깅 설정 (절대 경로 사용)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'inspect.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 모듈 import는 경로 설정 후에
from modules.auth import login_to_krcon

# 결과 저장 폴더
INSPECT_DIR = os.path.join(BASE_DIR, "output", "inspect_results")
os.makedirs(INSPECT_DIR, exist_ok=True)

def inspect_pdf_download(driver, url, page_name):
    """PDF 다운로드 방법 분석"""
    logger.info("="*80)
    logger.info(f"📄 페이지 분석: {page_name}")
    logger.info("="*80)
    logger.info(f"🔗 URL: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)
        
        logger.info(f"📍 실제 URL: {driver.current_url}")
        logger.info(f"📌 제목: {driver.title}")
        
        # 1. PDF 버튼 찾기
        logger.info("\n🔍 PDF 버튼 찾기:")
        logger.info("-"*80)
        
        try:
            pdf_button = driver.find_element(By.ID, "ankPrint")
            logger.info("✅ PDF 버튼 발견!")
            logger.info(f"   버튼 텍스트: {pdf_button.text}")
            logger.info(f"   href: {pdf_button.get_attribute('href')}")
            logger.info(f"   onclick: {pdf_button.get_attribute('onclick')}")
            
            # 2. PDF 버튼 클릭 테스트
            logger.info("\n📥 PDF 버튼 클릭 테스트:")
            logger.info("-"*80)
            
            # 현재 창 수 기록
            windows_before = driver.window_handles
            logger.info(f"   클릭 전 창 개수: {len(windows_before)}")
            
            # 버튼 클릭
            try:
                pdf_button.click()
                time.sleep(3)
                
                # 새 창 확인
                windows_after = driver.window_handles
                logger.info(f"   클릭 후 창 개수: {len(windows_after)}")
                
                if len(windows_after) > len(windows_before):
                    # 새 창으로 전환
                    new_window = [w for w in windows_after if w not in windows_before][0]
                    driver.switch_to.window(new_window)
                    
                    new_url = driver.current_url
                    logger.info(f"   ✅ 새 창 열림!")
                    logger.info(f"   새 창 URL: {new_url}")
                    logger.info(f"   새 창 제목: {driver.title}")
                    
                    # Blob URL 체크
                    if new_url.startswith("blob:"):
                        logger.warning("   ⚠️  Blob URL 감지! 직접 다운로드 불가")
                        
                        # iframe 확인
                        iframes = driver.find_elements(By.TAG_NAME, "iframe")
                        if iframes:
                            logger.info(f"   📦 iframe {len(iframes)}개 발견")
                            for idx, iframe in enumerate(iframes, 1):
                                src = iframe.get_attribute('src')
                                logger.info(f"      {idx}. {src or '(src 없음)'}")
                        
                        # embed 확인
                        embeds = driver.find_elements(By.TAG_NAME, "embed")
                        if embeds:
                            logger.info(f"   📦 embed {len(embeds)}개 발견")
                            for idx, embed in enumerate(embeds, 1):
                                src = embed.get_attribute('src')
                                logger.info(f"      {idx}. {src or '(src 없음)'}")
                    
                    elif new_url.endswith('.pdf') or 'pdf' in new_url.lower():
                        logger.info("   ✅ PDF URL 발견! 다운로드 가능")
                    
                    else:
                        logger.info("   ℹ️  PDF가 아닌 페이지")
                    
                    # 원래 창으로 복귀
                    driver.close()
                    driver.switch_to.window(windows_before[0])
                    
                else:
                    logger.info("   ℹ️  새 창이 열리지 않음 (같은 창에서 처리?)")
                    
                    # iframe 변화 확인
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    if iframes:
                        logger.info(f"   📦 iframe {len(iframes)}개 발견")
                        for idx, iframe in enumerate(iframes, 1):
                            src = iframe.get_attribute('src')
                            logger.info(f"      {idx}. {src or '(src 없음)'}")
                
            except Exception as e:
                logger.error(f"   ❌ 클릭 실패: {e}")
                
        except Exception as e:
            logger.warning(f"❌ PDF 버튼 없음: {e}")
        
        # 3. 페이지 소스 저장
        html_file = os.path.join(INSPECT_DIR, f"{page_name.replace(' ', '_')}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info(f"\n💾 페이지 소스 저장: {os.path.basename(html_file)}")
        
    except Exception as e:
        logger.error(f"❌ 분석 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("="*80)
    logger.info("🔍 KR-CON 페이지 구조 분석 도구")
    logger.info("="*80)
    
    # 테스트할 페이지들 (PDF가 있을 것 같은 페이지들)
    test_pages = [
        ("SOLAS 1974 Convention", "https://krcon.krs.co.kr/Functions/TreeView/View.aspx?LocaleKey=en&Id=8026"),
        ("Article I General Obligations", "https://krcon.krs.co.kr/Functions/TreeView/View.aspx?LocaleKey=en&Id=8027"),
        ("Amendment Status SOLAS 1974", "https://krcon.krs.co.kr/Functions/TreeView/View.aspx?LocaleKey=en&Id=4271"),
    ]
    
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    
    driver = None
    try:
        logger.info("\n🌐 Chrome 브라우저 시작...")
        driver = webdriver.Chrome(options=options)
        
        # 로그인
        if not login_to_krcon(driver):
            logger.error("❌ 로그인 실패")
            exit(1)
        
        # 각 페이지 분석
        for page_name, url in test_pages:
            inspect_pdf_download(driver, url, page_name)
            logger.info("\n" + "="*80 + "\n")
            time.sleep(2)
        
        logger.info("="*80)
        logger.info("✅ 분석 완료!")
        logger.info("="*80)
        logger.info(f"\n💡 결과 확인:")
        logger.info(f"   - {INSPECT_DIR}/*.html 파일")
        logger.info(f"   - {os.path.join(LOG_DIR, 'inspect.log')}")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  사용자 중단")
    except Exception as e:
        logger.error(f"❌ 에러: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if driver:
            driver.quit()
