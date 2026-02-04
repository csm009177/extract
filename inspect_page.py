"""
KR-CON 페이지 구조 분석 도구
- PDF 링크가 어떻게 구성되어 있는지 확인
- 다운로드 방법 파악
"""
import logging
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from auth import login_to_krcon

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# 결과 저장 폴더
INSPECT_DIR = "inspect_results"

def inspect_page(driver, url, page_name):
    """페이지 구조 분석"""
    logger.info("="*80)
    logger.info(f"📄 페이지 분석: {page_name}")
    logger.info("="*80)
    logger.info(f"🔗 URL: {url}\n")
    
    driver.get(url)
    time.sleep(3)
    
    # 현재 URL
    logger.info(f"📍 실제 URL: {driver.current_url}")
    
    # 페이지 타이틀
    logger.info(f"📌 제목: {driver.title}\n")
    
    # PDF 관련 링크 찾기
    logger.info("🔍 PDF 링크 찾기:")
    logger.info("-"*80)
    
    pdf_patterns = [
        ("a[href$='.pdf']", "확장자가 .pdf로 끝나는 링크"),
        ("a[href*='.pdf']", "URL에 .pdf 포함된 링크"),
        ("a[href*='Download']", "Download 포함된 링크"),
        ("a[href*='download']", "download 포함된 링크"),
        ("a[title*='PDF']", "title 속성에 PDF 포함"),
        ("a[title*='Download']", "title 속성에 Download 포함"),
        ("button[onclick*='.pdf']", "PDF 관련 버튼"),
        ("input[type='button'][value*='Download']", "Download 버튼"),
        (".download-link", "download-link 클래스"),
        (".pdf-link", "pdf-link 클래스")
    ]
    
    found_any = False
    
    for selector, description in pdf_patterns:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                logger.info(f"\n✅ [{description}]: {len(elements)}개 발견")
                for idx, elem in enumerate(elements[:3], 1):  # 최대 3개만 표시
                    try:
                        text = elem.text.strip() or "(텍스트 없음)"
                        href = elem.get_attribute('href') or elem.get_attribute('onclick') or "(속성 없음)"
                        logger.info(f"   {idx}. {text}")
                        logger.info(f"      → {href}")
                    except:
                        pass
                found_any = True
        except:
            pass
    
    if not found_any:
        logger.info("❌ PDF 링크를 찾을 수 없습니다!\n")
    
    # iframe 확인
    logger.info("\n🖼️  iframe 확인:")
    logger.info("-"*80)
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if iframes:
        logger.info(f"✅ {len(iframes)}개 iframe 발견")
        for idx, iframe in enumerate(iframes, 1):
            src = iframe.get_attribute('src') or "(src 없음)"
            logger.info(f"   {idx}. {src}")
    else:
        logger.info("❌ iframe 없음\n")
    
    # embed 태그 확인
    logger.info("\n📎 embed/object 태그 확인:")
    logger.info("-"*80)
    embeds = driver.find_elements(By.TAG_NAME, "embed")
    objects = driver.find_elements(By.TAG_NAME, "object")
    
    if embeds:
        logger.info(f"✅ {len(embeds)}개 embed 태그 발견")
        for idx, embed in enumerate(embeds, 1):
            src = embed.get_attribute('src') or "(src 없음)"
            logger.info(f"   {idx}. {src}")
    
    if objects:
        logger.info(f"✅ {len(objects)}개 object 태그 발견")
        for idx, obj in enumerate(objects, 1):
            data = obj.get_attribute('data') or "(data 없음)"
            logger.info(f"   {idx}. {data}")
    
    if not embeds and not objects:
        logger.info("❌ embed/object 태그 없음\n")
    
    # 모든 링크 분석
    logger.info("\n🔗 페이지 내 모든 링크 (PDF 관련 가능성):")
    logger.info("-"*80)
    all_links = driver.find_elements(By.TAG_NAME, "a")
    pdf_keywords = ['pdf', 'download', 'file', 'document', 'view', 'show']
    
    potential_pdf_links = []
    for link in all_links:
        try:
            href = link.get_attribute('href') or ""
            text = link.text.strip().lower()
            
            if any(keyword in href.lower() or keyword in text for keyword in pdf_keywords):
                potential_pdf_links.append((text or "(텍스트 없음)", href))
        except:
            pass
    
    if potential_pdf_links:
        logger.info(f"✅ {len(potential_pdf_links)}개 잠재적 PDF 링크 발견")
        for idx, (text, href) in enumerate(potential_pdf_links[:10], 1):
            logger.info(f"   {idx}. {text[:50]}")
            logger.info(f"      → {href}")
    else:
        logger.info("❌ 잠재적 PDF 링크 없음\n")
    
    # HTML 저장 (폴더에)
    os.makedirs(INSPECT_DIR, exist_ok=True)
    filename = os.path.join(INSPECT_DIR, f"{page_name.replace(' ', '_').replace(':', '_')}.html")
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    logger.info(f"\n💾 페이지 소스 저장: {filename}")
    
    # iframe 내부 콘텐츠 확인 (src가 있는 경우)
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for idx, iframe in enumerate(iframes, 1):
        src = iframe.get_attribute('src')
        if src and src != "about:blank":
            try:
                # iframe으로 전환
                driver.switch_to.frame(iframe)
                iframe_content = driver.page_source
                
                iframe_filename = os.path.join(INSPECT_DIR, f"{page_name.replace(' ', '_')}_iframe{idx}.html")
                with open(iframe_filename, 'w', encoding='utf-8') as f:
                    f.write(iframe_content)
                logger.info(f"   📄 iframe #{idx} 저장: {iframe_filename}")
                
                # 원래 페이지로 복귀
                driver.switch_to.default_content()
            except Exception as e:
                logger.debug(f"   ⚠️  iframe #{idx} 접근 실패: {e}")
                driver.switch_to.default_content()
    
    logger.info("\n" + "="*80 + "\n")

if __name__ == "__main__":
    logger.info("\n" + "="*80)
    logger.info("🔍 KR-CON 페이지 구조 분석 도구")
    logger.info("="*80 + "\n")
    
    # 결과 폴더 생성
    os.makedirs(INSPECT_DIR, exist_ok=True)
    logger.info(f"📁 결과 저장 폴더: {INSPECT_DIR}\n")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        
        # 로그인
        if not login_to_krcon(driver):
            logger.error("로그인 실패. 종료합니다.")
            exit(1)
        
        # 분석할 페이지들
        test_pages = [
            {
                "name": "KR-CON (English)",
                "url": "https://krcon.krs.co.kr/Functions/TreeView/List.aspx?LocaleKey=en&Tree=0000.00e0"
            },
            {
                "name": "Amendment Status SOLAS 1974",
                "url": "https://krcon.krs.co.kr/Functions/TreeView/View.aspx?LocaleKey=en&Id=4271"
            },
            {
                "name": "Article I General Obligations",
                "url": "https://krcon.krs.co.kr/Functions/TreeView/View.aspx?LocaleKey=en&Id=8026"
            }
        ]
        
        for page in test_pages:
            inspect_page(driver, page["url"], page["name"])
            time.sleep(2)
        
        logger.info("="*80)
        logger.info("✅ 분석 완료!")
        logger.info("="*80)
        logger.info(f"\n� 결과 폴더: {os.path.abspath(INSPECT_DIR)}")
        logger.info("\n�💡 생성된 파일:")
        logger.info(f"   - {INSPECT_DIR}/*.html (각 페이지의 소스)")
        logger.info("\n다음 단계:")
        logger.info(f"   1. {INSPECT_DIR} 폴더의 HTML 파일들을 브라우저로 열어 확인")
        logger.info("   2. PDF 다운로드 방법 파악 (iframe 주목!)")
        logger.info("   3. download_all.py 수정\n")
        
    except KeyboardInterrupt:
        logger.info("\n중단되었습니다.")
    except Exception as e:
        logger.error(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
