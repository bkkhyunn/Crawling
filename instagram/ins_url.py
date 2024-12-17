import os
import time
from datetime import datetime
import pytz
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import urllib
import re
import shutil
import json


def load_config():
    with open("./config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    username = config["login"]["username"]
    password = config["login"]["password"]
    keywords = config["keywords"]
    iter = config["iter"]
    user_agent = config["headers"]["user-agent"]

    return username, password, keywords, iter, user_agent


def main():
    user_id, password, keywords, iter, user_agent = load_config()
    driver = webdriver.Chrome()

    # 한국 표준시 설정
    kst = pytz.timezone("Asia/Seoul")
    current_time = datetime.now(kst)
    current_datetime = current_time.strftime("%Y%m%d_%H%M%S")

    csv_path = "./urls/url.csv"  # 기존에 저장되어 있던 url
    new_csv_path = "./urls/new_url_{}.csv".format(
        current_datetime
    )  # 이번에 새로 모이는 데이터들

    # 기존 CSV 파일이 없으면 새로 생성
    if not os.path.exists(csv_path):
        df = pd.DataFrame(columns=["keyword", "url", "full_text"])
        df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"새로운 CSV 파일 생성: {csv_path}")

    if not os.path.exists(new_csv_path):
        df = pd.DataFrame(columns=["keyword", "url", "full_text"])
        df.to_csv(new_csv_path, index=False, encoding="utf-8")
        print(f"새로운 CSV 파일 생성: {new_csv_path}")

    # 백업 파일 하나 생성
    back_up = "./urls/url_backup.csv"
    shutil.copyfile(csv_path, back_up)

    Data_List = []  # 데이터 저장 리스트

    # Instagram 접속 및 로그인
    url = "https://www.instagram.com/"
    driver.get(url)
    time.sleep(6)
    user = driver.find_element(
        By.XPATH, '//*[@id="loginForm"]/div/div[1]/div/label/input'
    )
    user.send_keys(user_id)
    driver.find_element(
        By.XPATH, '//*[@id="loginForm"]/div/div[2]/div/label/input'
    ).send_keys(password)
    driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[3]/button/div').click()
    time.sleep(80)

    index = 0  # 키워드 인덱스
    dup_count = 0  # 총 중복 개수

    while index < len(keywords):
        word = keywords[index]
        print(word)

        if not word:
            print("키워드가 비어 있습니다!")
            index += 1
            continue

        word = urllib.parse.quote(word)
        word_url = f"https://www.instagram.com/explore/tags/{word}/"
        driver.get(word_url)

        key_dup_count = 0
        try:
            page = 0
            for y in range(iter):  # 크롤링 반복 횟수 설정
                time.sleep(5)
                js = "window.scrollBy(0,1000)"
                driver.execute_script(js)
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")

                divimg = soup.find_all(
                    "img",
                    {"class": "x5yr21d xu96u03 x10l6tqk x13vifvy x87ps6o xh8yej3"},
                )
                if not divimg:
                    print("이미지를 찾을 수 없습니다.")
                    continue

                for div in divimg:
                    content = div.get("alt")
                    if not content:
                        print("내용이 없습니다.")
                        continue

                    data = []
                    a = div.find_parent("a")
                    if a is None:
                        print("게시물 링크가 잘못되었습니다.")
                        continue
                    urlto = a.get("href")
                    if urlto is None:
                        print("게시물 링크가 없습니다.")
                        continue
                    totalurl = "https://www.instagram.com" + urlto
                    data.append(keywords[index])
                    data.append(totalurl)

                    modified_content = re.sub(r"\s*\n\s*", " ", content)
                    data.append(modified_content)

                    Data_List.append(data)

                page += 1
                print(f"페이지 {page}에서 데이터를 가져오는 중...")
                time.sleep(5)

        except Exception as e:
            print(e)
            print("오류 발생")

        print(f"키워드 {keywords[index]}의 URL 정보 수집 완료.")

        # 중복 제거
        Data_List_New = []
        for data in Data_List:
            if data not in Data_List_New:
                Data_List_New.append(data)
            else:
                key_dup_count += 1

        print(
            f"키워드 {keywords[index]}에서 {key_dup_count} 개의 중복 제거 후, 총 {len(Data_List_New)} 개의 데이터 크롤링 완료!"
        )
        df_Sheet = pd.DataFrame(Data_List_New, columns=["keyword", "url", "full_text"])

        df = pd.read_csv(
            csv_path, encoding="utf-8", usecols=["keyword", "url", "full_text"]
        )
        unique_df = pd.read_csv(
            new_csv_path, encoding="utf-8", usecols=["keyword", "url", "full_text"]
        )

        file = [df, df_Sheet]
        new_df = pd.concat(file, axis=0)

        uniq_data = df_Sheet.merge(
            df, on=["keyword", "url", "full_text"], how="left", indicator=True
        )
        uniq_data = uniq_data[uniq_data["_merge"] == "left_only"].drop(columns="_merge")
        uniq_file = [unique_df, uniq_data]
        new_uniq_df = pd.concat(uniq_file, axis=0)

        # 전체 URL CSV 갱신
        final_df = new_df.drop_duplicates(
            subset=None, keep="first", inplace=False, ignore_index=True
        )
        final_df.to_csv(csv_path, index=False, encoding="utf-8")

        # 새로운 URL CSV 갱신
        final_uniq_df = new_uniq_df.drop_duplicates(
            subset=None, keep="first", inplace=False, ignore_index=True
        )
        final_uniq_df.to_csv(new_csv_path, index=False, encoding="utf-8")

        index += 1
        dup_count += key_dup_count

    driver.close()

    # 최종 중복 제거 및 저장
    Data_List_New = []
    for data in Data_List:
        if data not in Data_List_New:
            Data_List_New.append(data)
        else:
            dup_count += 1

    print("-------------------------------------")
    print(
        f"{dup_count} 개의 중복 제거 후, 총 {len(Data_List_New)} 개의 새로운 데이터를 크롤링했습니다."
    )
    df_Sheet = pd.DataFrame(Data_List_New, columns=["keyword", "url", "full_text"])
    df = pd.read_csv(
        csv_path, encoding="utf-8", usecols=["keyword", "url", "full_text"]
    )
    unique_df = pd.read_csv(
        new_csv_path, encoding="utf-8", usecols=["keyword", "url", "full_text"]
    )

    file = [df, df_Sheet]
    new_df = pd.concat(file, axis=0)

    uniq_data = df_Sheet.merge(
        df, on=["keyword", "url", "full_text"], how="left", indicator=True
    )
    uniq_data = uniq_data[uniq_data["_merge"] == "left_only"].drop(columns="_merge")
    uniq_file = [unique_df, uniq_data]
    new_uniq_df = pd.concat(uniq_file, axis=0)

    # 전체 URL CSV 갱신
    final_df = new_df.drop_duplicates(
        subset=None, keep="first", inplace=False, ignore_index=True
    )
    final_df.to_csv(csv_path, index=False, encoding="utf-8")

    # 새로운 URL CSV 갱신
    final_uniq_df = new_uniq_df.drop_duplicates(
        subset=None, keep="first", inplace=False, ignore_index=True
    )
    final_uniq_df.to_csv(new_csv_path, index=False, encoding="utf-8")


if __name__ == "__main__":
    main()
