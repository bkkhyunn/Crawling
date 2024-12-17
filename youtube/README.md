## Youtube Crawling

```bash
python main.py --config [config.json 경로] --period [week or month] --step [1, 2, 3, 4] --data_path [data 폴더 경로] --date_op [yyyy-mm-dd] --save_batch [number]
```

- `--config` : brand keyword 와 user-agent 가 있는 config.json 파일 경로
- `--period` : 1주일, 1달 선택. `--date_op` 를 사용할 경우 입력하지 않아도 됨.
- `--step`
  - `1` : 검색 크롤링만
  - `2` : 영상 설명 크롤링만
  - `3` : youtube.csv 최신화만
  - `4`(default) : 전체 작업 실시
- `--data_path` : data 저장 경로. `main.py` 실행 시 하위 폴더로 `pre`, `post`, `backup` 폴더가 자동으로 생성됨.
- `--date_op` : youtube 고급검색 옵션. `2024-12-01` 과 같이 정확한 형태로 건네주어야 함.
- `--save_batch` : 데이터 저장 주기 옵션. default 는 1 로 하나 수집할 때마다 csv 파일을 최신화.

```text
├── README.md
├── __init__.py
├── config.json         # brand keyword, user-agent
├── main.py            
├── utils.py            # scroll 등 함수
└── youtube_crawler.py  # crawler
```