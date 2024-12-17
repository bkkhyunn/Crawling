from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from utils import load_config, scroll, start_driver

import pandas as pd
import time
import random
from datetime import datetime
import re
import os
import glob
import shutil
from tqdm import tqdm


class Youtube_Crawler:
    def __init__(self, args):
        self.config = args.config  # config.json 주소
        self.period = args.period  # week or month
        self.step = args.step  # 1, 2, 3, 4
        self.data_path = args.data_path  # data 폴더 경로
        self.date_op = args.date_op  # date operation 사용 여부
        self.save_batch = args.save_batch  # 데이터 저장 주기

    def search_crawling(self):
        """
        검색 및 필터링 후 키워드, 영상제목, 영상 제작자, 링크, 쇼츠여부, 섬네일 이미지 수집
        """
        keywords, user_agent = load_config(self.config)
        driver = start_driver(user_agent)

        current_time = datetime.now()
        ctime = current_time.strftime("%y%m%d%H%M%S")

        results = os.path.join(self.data_path, f"pre/youtube_{ctime}.csv")
        if not os.path.exists(results):
            df = pd.DataFrame(
                columns=[
                    "keywords",
                    "title",
                    "channel_owner",
                    "link",
                    "is_shorts",
                    "thumbnail",
                ]
            )
            df.to_csv(results, index=False, encoding="utf-8")
            print(f"새로운 CSV 파일 생성: {results}")

        c1 = datetime.now()
        print(f"{c1} 검색 크롤링 시작", end="\n")

        # 크롤링 개수 제한
        keywords = keywords[622:]

        for keyword in tqdm(keywords, total=len(keywords), desc="크롤링 진행 중"):
            SEARCH_KEYWORD = keyword.replace(" ", "+")

            if self.date_op:
                # &sp=CAASAhAB: 동영상, 관련성  /  &sp=CAI%253D: 동영상, 업로드 날짜
                FILTERING = "&sp=CAI%253D"
                DATE_OP = f"after:{self.date_op}"
                URL = (
                    "https://www.youtube.com/results?search_query="
                    + SEARCH_KEYWORD
                    + DATE_OP
                    + FILTERING
                )
                print("URL : " + URL)
                driver.get(URL)
                scroll(driver)
                time.sleep(1.5)

            else:
                URL = "https://www.youtube.com/results?search_query=" + SEARCH_KEYWORD
                print("URL : " + URL)
                driver.get(URL)
                time.sleep(1.5)

                # 동영상 - 필터(이번주) - 필터(업로드 날짜)
                driver.find_element(
                    By.XPATH, '//*[@id="chips"]/yt-chip-cloud-chip-renderer[3]'
                ).click()  # 동영상만
                driver.find_element(
                    By.XPATH,
                    '//*[@id="filter-button"]/ytd-button-renderer/yt-button-shape/button/yt-touch-feedback-shape/div',
                ).click()  # 필터 클릭
                time.sleep(0.5)

                if self.period == "week":
                    driver.find_element(
                        By.CSS_SELECTOR,
                        "#options > ytd-search-filter-group-renderer:nth-child(1) > ytd-search-filter-renderer:nth-child(6) a",
                    ).click()  # 이번 주 클릭

                elif self.period == "month":
                    driver.find_element(
                        By.CSS_SELECTOR,
                        "#options > ytd-search-filter-group-renderer:nth-child(1) > ytd-search-filter-renderer:nth-child(8) a",
                    ).click()  # 이번 달 클릭

                time.sleep(2)
                driver.find_element(
                    By.XPATH,
                    '//*[@id="filter-button"]/ytd-button-renderer/yt-button-shape/button/yt-touch-feedback-shape/div',
                ).click()  # 필터 클릭
                time.sleep(0.5)
                driver.find_element(
                    By.CSS_SELECTOR,
                    "#options > ytd-search-filter-group-renderer:nth-child(5) > ytd-search-filter-renderer:nth-child(4) a",
                ).click()  # 업로드 날짜 클릭
                time.sleep(2)

                scroll(driver)
                time.sleep(3)

            # 페이지 소스 추출
            html_source = driver.page_source
            soup_source = BeautifulSoup(html_source, "html.parser")

            # 콘텐츠 정보 추출
            content_total = soup_source.find_all(
                "a",
                {
                    "id": "video-title",
                    "class": "yt-simple-endpoint style-scope ytd-video-renderer",
                },
            )
            content_total_title = list(
                map(lambda data: data.get("title").replace("\n", ""), content_total)
            )  # 제목
            content_total_link = list(
                map(
                    lambda data: "https://youtube.com" + data.get("href"), content_total
                )
            )  # 링크

            # 섬네일 이미지 추출
            content_image = []
            for link in content_total_link:
                if "shorts" in link:
                    video_id = link.split("/")[-1]
                    content_image.append(
                        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    )
                else:
                    match = re.search(r"v=([^&]+)", link)
                    if match:
                        video_id = match.group(1)
                        content_image.append(
                            f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                        )
                    else:
                        content_image.append("-")

            content_total_info = list(
                map(lambda data: data.get("aria-label"), content_total)
            )
            content_total_channel_owner = []  # 영상 제작자 채널
            is_shorts = []  # 쇼츠 여부
            pattern = r"게시자:\s*(.+?)\s+조회수\s+(없음|\d[\d,]*회)\s+(?:스트리밍\s+시간:\s+)?((?:\d+(?:개월|주|일|시간|분|초)\s*전)?)\s*((?:\d+분)?(?:\s*\d+초)?)"

            for text in content_total_info:
                if "Shorts 동영상 재생" in text:
                    is_shorts.append("Shorts")
                else:
                    is_shorts.append("Video")

                match = re.search(pattern, text)
                if match:
                    content_total_channel_owner.append(match.group(1))
                else:
                    content_total_channel_owner.append("-")

            # 딕셔너리 formatting
            content_total_dict = {
                "keywords": [keyword] * len(content_total_title),
                "title": content_total_title,
                "channel_owner": content_total_channel_owner,
                "link": content_total_link,
                "is_shorts": is_shorts,
                "thumbnail": content_image,
            }

            df = pd.read_csv(
                results,
                encoding="utf-8",
                usecols=[
                    "keywords",
                    "title",
                    "channel_owner",
                    "link",
                    "is_shorts",
                    "thumbnail",
                ],
            )
            df2 = pd.DataFrame(content_total_dict)
            new_df = pd.concat([df, df2], axis=0)
            final_df = new_df.drop_duplicates(
                subset=None, keep="first", inplace=False, ignore_index=True
            )
            final_df.to_csv(results, index=False, encoding="utf-8")

            time.sleep(random.uniform(1, 5))

        driver.quit()

        c2 = datetime.now()
        print(f"{c2} 검색 크롤링 끝!", end="\n")
        elapsed_time = c2 - c1
        print(f"검색 크롤링 총 작업 시간: {elapsed_time}")
        print()

    def description_crawling(self):
        """
        영상 설명란 정보, 채널 id, 비디오 길이, 조회 수, 영상 업로드 날짜 얻어오기. 정보를 얻어오면 그 즉시 저장하고 업데이트
        """

        folder_path = os.path.join(self.data_path, "pre")
        file_pattern = os.path.join(folder_path, "youtube_*.csv")
        files = glob.glob(file_pattern)

        if files:
            latest_file = max(files, key=os.path.getctime)
            print(f"최신 파일: {latest_file}")
        else:
            print("해당 폴더에 'youtube_'로 시작하는 파일이 없습니다.")

        df = pd.read_csv(
            latest_file,
            encoding="utf-8",
            usecols=[
                "keywords",
                "title",
                "channel_owner",
                "link",
                "is_shorts",
                "thumbnail",
            ],
        )

        # 결과 저장 파일
        results = os.path.join(self.data_path, f"post/{os.path.basename(latest_file)}")

        # 이미 처리된 데이터 불러오기
        if os.path.exists(results):
            processed_df = pd.read_csv(results, encoding="utf-8")
            processed = set(
                processed_df[["keywords", "title", "link"]]
                .apply(tuple, axis=1)
                .tolist()
            )
            print(f"이미 처리된 URL 개수: {len(processed)}")
        else:
            processed_df = pd.DataFrame(
                columns=df.columns.tolist()
                + [
                    "channel_owner_id",
                    "video_description",
                    "video_length",
                    "view_count",
                    "upload_date",
                ]
            )
            processed = set()

        _, user_agent = load_config(self.config)
        driver = start_driver(user_agent)

        c1 = datetime.now()
        print(f"{c1} 영상 설명 크롤링 시작!", end="\n")

        error_log = []  # 에러 발생한 URL 수집
        batch = self.save_batch  # 데이터 저장 주기. 현재는 1개씩 진행하고 이후 안정화되면 50개 내지는 100개로 하면 좋을 듯

        try:
            for i in tqdm(range(len(df)), total=len(df), desc="크롤링 진행 중"):
                row = df.iloc[i, :]
                check = (
                    row["keywords"],
                    row["title"],
                    row["link"],
                )
                URL = row["link"]

                # 이미 처리된 데이터는 건너뛰기
                if check in processed:
                    continue

                try:
                    driver.get(URL)
                    time.sleep(2)

                    html = driver.page_source
                    soup = BeautifulSoup(html, "html.parser")

                    script_tag = soup.select_one("body > script")
                    script = script_tag.get_text() if script_tag else ""

                    channel_owner_id_re = (
                        r'"ownerProfileUrl":"http://www.youtube.com/@(.*?)"'
                    )
                    description_re = r'description":{"simpleText":"(.*?)"},'
                    length_re = r'},"lengthSeconds":"(.*?)","ownerProfileUrl"'
                    view_re = r'"viewCount":"(.*?)",'
                    upload_date_re = r'"publishDate":"(.*?)","ownerChannelName'

                    channel_owner_id = re.search(
                        channel_owner_id_re, script
                    )  # 채널 제작자 id
                    description = re.search(description_re, script)  # 영상 세부 설명
                    length = re.search(length_re, script)  # 영상 길이
                    view = re.search(view_re, script)  # 조회수
                    upload_date = re.search(upload_date_re, script)  # 업로드 날짜

                    channel_owner_id = (
                        channel_owner_id.group(1) if channel_owner_id else "-"
                    )
                    description = description.group(1) if description else "-"
                    length = length.group(1) if length else "-"
                    view = view.group(1) if view else "-"
                    upload_date = upload_date.group(1) if upload_date else "-"

                except Exception as e:
                    print(f"URL {URL} 에서 에러 발생: {e}")
                    error_log.append((URL, e))
                    channel_owner_id, description, length, view, upload_date = (
                        "-",
                        "-",
                        "-",
                        "-",
                        "-",
                    )

                # 새 데이터를 처리된 데이터프레임에 추가
                new_row = pd.DataFrame(
                    [
                        [
                            row["keywords"],
                            row["title"],
                            row["channel_owner"],
                            row["link"],
                            row["is_shorts"],
                            row["thumbnail"],
                            channel_owner_id,
                            description,
                            length,
                            view,
                            upload_date,
                        ]
                    ],
                    columns=processed_df.columns,
                )

                processed_df = pd.concat([processed_df, new_row], ignore_index=True)
                processed.add(check)

                if i % batch == 0:
                    processed_df.to_csv(results, index=False, encoding="utf-8")

                time.sleep(random.uniform(1, 3))

        finally:
            driver.quit()

        # 에러 로그 저장
        if error_log:
            with open(f"./error_urls_{c1}.txt", "w") as f:
                for url, error in error_log:
                    f.write(f"{url} -> {error} \n")

        c2 = datetime.now()
        print(f"{c2} 영상 설명 크롤링 끝!", end="\n")
        elapsed_time = c2 - c1
        print(f"영상 설명 크롤링 총 작업 시간: {elapsed_time}")
        print()

    def update_data(self):
        """
        youtube_data.csv 최신화
        """
        c1 = datetime.now()
        # 파일 경로 설정
        data = os.path.join(self.data_path, "youtube_data.csv")
        folder_path = os.path.join(self.data_path, "post")

        # ./data/youtube_data.csv가 없을 경우 csv 생성
        if not os.path.exists(data):
            print(f"'{data}' 파일이 없습니다. 기본 파일을 생성합니다.")
            default_df = pd.DataFrame(
                columns=[
                    "keywords",
                    "title",
                    "channel_owner",
                    "link",
                    "is_shorts",
                    "thumbnail",
                    "channel_owner_id",
                    "video_description",
                    "video_length",
                    "view_count",
                    "upload_date",
                ]
            )
            default_df.to_csv(data, index=False, encoding="utf-8")

        # youtube_data.csv 백업
        current_time = datetime.now()
        ctime = current_time.strftime("%y%m%d%H%M%S")
        backup_file = os.path.join(self.data_path, f"backup/youtube_data_{ctime}.csv")
        shutil.copyfile(data, backup_file)

        # 최신 파일 찾기
        file_pattern = os.path.join(folder_path, "youtube_*.csv")
        files = glob.glob(file_pattern)

        if files:
            latest_file = max(files, key=os.path.getctime)
            print(f"최신 파일: {latest_file}")
        else:
            print("해당 폴더에 'youtube_'로 시작하는 파일이 없습니다.")

        post_df = pd.read_csv(latest_file, encoding="utf-8", lineterminator="\n")
        post_df_len = len(post_df)
        df = pd.read_csv(data, encoding="utf-8", lineterminator="\n")
        df_len = len(df)

        # 데이터 결합
        new_df = pd.concat([post_df, df], axis=0)
        new_df.sort_values(by="keywords", ascending=True, inplace=True)

        # 중복 제거
        new_df["source"] = ["post_df"] * len(post_df) + ["df"] * len(df)
        new_df.drop_duplicates(
            subset=["keywords", "title", "channel_owner", "link", "channel_owner_id"],
            keep="first",
            inplace=True,
            ignore_index=True,
        )
        new_df.drop(columns=["source"], inplace=True)

        new_df_len = len(new_df)
        c2 = datetime.now()
        # 결과 출력 및 저장
        print(
            f"새로운 데이터 개수: {post_df_len} 현재 데이터 개수: {df_len} 합친 데이터 개수: {new_df_len}"
        )
        new_df.to_csv(data, index=False, encoding="utf-8")

        elapsed_time = c2 - c1
        print(f"데이터 최신화 총 작업 시간: {elapsed_time}")
        print()
