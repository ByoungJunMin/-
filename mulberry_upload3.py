import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ChromeDriver 설정
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_driver_path = r"C:\Program Files\Google\Chrome\Application\chromedriver-win64\chromedriver.exe"

service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Mulberry 웹 페이지 열기 (Selenium으로 직접 로드)
url = "https://www.mulberry.com/kr/shop/women/bags"
driver.get(url)
wait = WebDriverWait(driver, 20)  # 대기 시간을 20초로 설정
wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'img')))


# 쿠키 허용 팝업 처리
try:
    wait = WebDriverWait(driver, 10)
    cookie_button = wait.until(EC.element_to_be_clickable(
        (By.ID, 'onetrust-accept-btn-handler')))  # 쿠키 허용 버튼이 클릭 가능할 때까지 대기
    cookie_button.click()
    print("쿠키 허용 버튼 클릭")
except Exception as e:
    print(f"쿠키 허용 버튼 클릭 실패: {e}")

# 페이지 끝까지 스크롤하여 모든 제품 로드
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)  # 스크롤 후 페이지 로드 대기
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# 동적 콘텐츠 로드 대기
try:
    wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'list-item.product')))
    print("모든 제품 로드 완료")
except Exception as e:
    print(f"동적 콘텐츠 로드 실패: {e}")

# 페이지 HTML 가져오기
soup = BeautifulSoup(driver.page_source, 'html.parser')

# 제품 정보 추출
products = []

# 각 제품 블록을 선택
product_blocks = soup.find_all('div', class_='list-item product')

for product in product_blocks:
    # 상품명 추출
    product_name = product.find('h3', class_='list-item__title').text.strip()
    
    # 판매가 추출
    price = product.find('span', itemprop='price').text.strip()
    
    # 옵션 (컬러) 추출
    color_tag = product.find('div', class_='available-colors')
    color = color_tag.text.strip() if color_tag else '정보 없음'
    
    # 링크 추출
    link = product.find('a', class_='list-item__figure link-product')['href']
    full_link = f"https://www.mulberry.com{link}"
    
    # 이미지 소스 추출
    image_tag = product.find('img')
    if image_tag:
        # srcset과 src 속성 추출
        image_srcset = image_tag.get('srcset')
        image_src = image_tag.get('src')
        
        # srcset이 존재하는 경우 첫 번째 URL을 선택
        if image_srcset:
            # srcset은 쉼표로 구분된 URL 목록을 가지므로, 첫 번째 URL을 사용
            image = image_srcset.split(',')[0].split(' ')[0]
        elif image_src:
            # src가 존재하는 경우 사용
            image = image_src
        else:
            # src와 srcset 모두 없는 경우
            image = '이미지 없음'
    else:
        # img 태그가 없는 경우
        image = '이미지 없음'
    print(f"이미지 태그: {image_tag}")
    print(f"srcset: {image_srcset}")
    print(f"src: {image_src}")

    # 제품 데이터를 리스트로 저장
    products.append([product_name, price, color, full_link, image])

# Pandas DataFrame 생성 및 Excel로 저장
df = pd.DataFrame(products, columns=['상품명', '판매가', '옵션(컬러)', '링크', '이미지소스'])
df.to_excel('mulberry_products.xlsx', index=False, engine='openpyxl')

# Selenium 종료
driver.quit()

print(f"크롤링 완료: 데이터가 'mulberry_products.xlsx'에 저장되었습니다.")
