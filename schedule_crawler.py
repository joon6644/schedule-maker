from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from io import StringIO 

# 브라우저 열기
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://msi.mju.ac.kr/") 

print("🛑 [중요] 로그인하고 '시간표 조회' 화면까지 이동하세요!")
print("🛑 준비되면 엔터(Enter)를 누르세요.")
input() 

all_data = []

# 1페이지부터 130페이지까지 한 땀 한 땀
for page in range(1, 131):
    print(f"📄 {page} / 130 페이지 수집 중...")
    
    try:
        # 1. 데이터 수집
        dfs = pd.read_html(StringIO(driver.page_source))
        real_table = max(dfs, key=len) 
        all_data.append(real_table)
        
        # 2. [핵심 수정] 버튼 클릭 대신 '페이지 이동 함수'를 강제 실행
        # go_page(2), go_page(3)... 이렇게 직접 명령을 내립니다.
        driver.execute_script(f"go_page({page + 1})") 
        
        time.sleep(1) # 페이지 로딩 대기 (너무 빠르면 서버가 싫어함)
            
    except Exception as e:
        print(f"⚠️ {page}페이지에서 문제 발생 (아마 마지막 페이지?): {e}")
        break

# 저장
if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    # 중복 제거 (혹시 모르니)
    final_df = final_df.drop_duplicates()
    
    final_df.to_csv("명지대_전체시간표_완성본.csv", index=False, encoding="utf-8-sig")
    print(f"🎉 성공! 총 {len(final_df)}개 강의를 꽉 채워 담았습니다.")
else:
    print("❌ 데이터를 못 가져왔습니다.")