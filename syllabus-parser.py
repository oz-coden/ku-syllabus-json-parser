import re
import json
import time
import datetime
import argparse
import sys
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict

class SyllabusScraper:
    def __init__(self, fiscal_year: Optional[int] = None):
        if fiscal_year:
            self.fiscal_year = str(fiscal_year)
        else:
            now = datetime.datetime.now()
            self.fiscal_year = str(now.year if now.month >= 4 else now.year - 1)

        self.code_mapping = {
            "11": "N10", "12": "N13", "18": "N16", "21": "N11", "22": "N14", "28": "N17",
            "13A": "110", "13B": "120", "13C": "180", "13D": "140", "13E": "310",
            "13F": "160", "13G": "320", "13H": "330", "23A": "150", "23B": "130", "23C": "170"
        }
        for prefix in ["13W", "13X", "13Y", "13Z"]:
            self.code_mapping[prefix] = "N20"

    def check_input_type(self, user_input: str) -> str:
        pattern = re.compile(r"^[1-2][0-9][a-zA-Z]{2}[0-9]{3}$")
        if user_input.startswith("https://"):
            return "url"
        elif pattern.match(user_input):
            return "code"
        return "invalid"

    def make_syllabus_link(self, code: str) -> Optional[str]:
        course_type = next((v for k, v in self.code_mapping.items() if code.startswith(k)), None)
        
        if not course_type:
            return None
            
        return f"https://webstation-koukai.kanagawa-u.ac.jp/syllabus/{self.fiscal_year}/{course_type}/{course_type}_{code}_ja_JP.html"

    def get_syllabus_info(self, url: str) -> Optional[Dict[str, str]]:
        try:
            time.sleep(1)
            
            response = requests.get(url, timeout=10)
            response.raise_for_status() 
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            
            course_info = {}
            
            for tr in soup.find_all('tr'):
                th = tr.find('th')
                td = tr.find('td')
                if th and td:
                    key = th.get_text(strip=True).replace(" ", "").replace("：", "")
                    value = td.get_text(separator="\n", strip=True)
                    if key and value:
                        course_info[key] = value
                        
            return course_info if course_info else None
            
        except requests.RequestException:
            return None

def main():
    parser = argparse.ArgumentParser(description="シラバス情報をJSON形式で取得するためのツール")
    parser.add_argument("query", help="時間割コードまたはURL")
    parser.add_argument("-y", "--year", type=int, help="取得する年度（省略時は現在の年度に基づく）", default=None)
    
    args = parser.parse_args()

    scraper = SyllabusScraper(fiscal_year=args.year)
    user_input = args.query.strip()
    input_type = scraper.check_input_type(user_input)

    if input_type == "invalid":
        print(json.dumps({"error": "正しくない形式です。URLか時間割コードを入力してください。"}, ensure_ascii=False))
        sys.exit(1)

    url = user_input if input_type == "url" else scraper.make_syllabus_link(user_input.upper())
    
    if not url:
        print(json.dumps({"error": "不明な時間割コードの形式です。"}, ensure_ascii=False))
        sys.exit(1)

    course_info = scraper.get_syllabus_info(url)
    
    if not course_info:
        print(json.dumps({"error": "データの取得に失敗しました。URLやコードが間違っているか、ページが存在しません。"}, ensure_ascii=False))
        sys.exit(1)

    print(json.dumps(course_info, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()