## Instagram Crawling

- instagram 대상 크롤링 후 이미지 ocr
- instagram 으로부터 ip 차단 당하기 쉬움 -> 프록시 사용 고려

```bash
python ins_url.py
python ins_data.py
python make_ocr_text.py
```

- `.py` 파일 별로 실행. 이후 모듈화 필요

```
ins_crawl_ocr
├── config.json      # 로그인 정보(id, pw), search keyword, 반복횟수
├── ins_url.py       # url 수집
├── ins_data.py      # 수집된 url 을 가지고 크롤링
├── make_ocr_text.py # 수집된 이미지 대상으로 ocr
├── results          # ins_data, make_ocr_text 결과
└── urls             # ins_url 결과
```
