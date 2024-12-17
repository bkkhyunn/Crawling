import os
import time
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import requests
import re
import glob
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

    # 최초에는 url 이 new_url 이기 때문에 new_url.csv 에 아무런 내용이 없으니, url.csv 로 데이터 수집 해야함.
    # initial_csv = './url/url.csv'
    folder_path = "./urls/"
    file_pattern = os.path.join(folder_path, "new_url*.csv")
    files = glob.glob(file_pattern)

    if files:
        latest_file = max(files, key=os.path.getctime)
        print(f"최신 파일: {latest_file}")
    else:
        print("해당 폴더에 'new_url'로 시작하는 파일이 없습니다.")

    # urls = pd.read_csv(initial_csv, encoding='utf-8', usecols=['keyword', 'url', 'full_text'])
    urls = pd.read_csv(
        latest_file, encoding="utf-8", usecols=["keyword", "url", "full_text"]
    )

    # 최종 데이터가 될 results
    results = "./results/data.csv"
    # 기존 CSV 파일이 없으면 새로 생성
    if not os.path.exists(results):
        df = pd.DataFrame(
            columns=[
                "brand",
                "username",
                "date",
                "post_url",
                "full_text",
                "like",
                "saved_imgs",
            ]
        )
        df.to_csv(results, index=False, encoding="utf-8")
        print(f"새로운 CSV 파일 생성: {results}")

    data_df = pd.read_csv(
        results,
        encoding="utf-8",
        usecols=[
            "brand",
            "username",
            "date",
            "post_url",
            "full_text",
            "like",
            "saved_imgs",
        ],
    )

    # 백업 파일 하나 생성
    back_up = "./results/data_backup.csv"
    shutil.copyfile(results, back_up)

    Data_List = []  # 데이터 저장 리스트

    # Instagram 접속 및 로그인
    driver = webdriver.Chrome()

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

    patient = 0  # 크롤링 에러
    image_patient = 0  # 이미지 수집 에러
    for idx, row in urls.iterrows():
        brand, post_url, full_text = row

        if post_url in data_df["post_url"].values:
            continue

        data = []
        driver.get(post_url)
        print(idx, ". " + post_url)

        try:
            time.sleep(5)
            html = driver.page_source
            soup = BeautifulSoup(html, "lxml")

            # 작성자
            username = soup.find(
                "span", {"class": "_ap3a _aaco _aacw _aacx _aad7 _aade"}
            ).text
            print(username, end=" ")

            # 작성일자
            date = soup.find_all("time")[-1]["datetime"][:10]
            print(date, end=" ")

            # like 개수
            try:
                like = soup.find(
                    "span",
                    {
                        "class": "html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs"
                    },
                ).text
            except Exception:
                like = "no data"  # ~~외 여러 명이 좋아합니다. 같은 경우
            print(like)

            # 이미지 저장
            images = []
            img_urls = set()
            images.append(
                driver.find_elements(
                    By.CLASS_NAME, "x5yr21d.xu96u03.x10l6tqk.x13vifvy.x87ps6o.xh8yej3"
                )
            )

            for i in range(len(images)):
                for j in range(len(images[i])):
                    if j >= 3:  # 4번째부터 타 게시물의 썸네일 이미지
                        break

                    alt = images[i][j].get_attribute("alt")
                    check = re.findall(r"by .+? on", alt)  # 타 게시물인지 아닌지 검사

                    if check != []:
                        img_urls.add(images[i][j].get_attribute("src"))

            try:
                while True:
                    time.sleep(3)

                    driver.find_element(
                        By.CLASS_NAME, "_afxw._al46._al47"
                    ).click()  # 다음 이미지 버튼 클릭
                    images.append(
                        driver.find_elements(
                            By.CLASS_NAME,
                            "x5yr21d.xu96u03.x10l6tqk.x13vifvy.x87ps6o.xh8yej3",
                        )
                    )

                    for i in range(len(images)):
                        for j in range(len(images[i])):
                            if j >= 3:  # 4번째부터 타 게시물의 썸네일 이미지
                                break

                            alt = images[i][j].get_attribute("alt")
                            check = re.findall(
                                r"by .+? on", alt
                            )  # 타 게시물인지 아닌지 검사

                            if check != []:
                                img_urls.add(images[i][j].get_attribute("src"))

                    images.clear()

            except Exception:
                print("더 이상 넘길 이미지 없음")

                img_urls = list(img_urls)
                if len(img_urls) == 0:
                    image_patient += 1
                else:
                    image_patient = 0

                if image_patient > 5:
                    break
                # print(img_urls)
                images.clear()

            data.append(brand)
            data.append(username)
            data.append(date)
            data.append(post_url)
            data.append(full_text)
            data.append(like)

            saved_imgs = set()
            for img_url in img_urls:
                # 이미지만 고려. 우선 비디오 타입은 고려하지 않음.
                pattern = r"\/v\/[^\/]+\/([^\/\?]+)\.(jpg|png|webp|heic)"
                match = re.search(pattern, img_url)
                if match:
                    img_name = match.group(1) + "." + match.group(2)
                else:
                    print("파일을 찾을 수 없거나 jpg 혹은 png, webp, heic 파일이 아님.")
                    continue

                if img_name not in saved_imgs:
                    response = requests.get(img_url, headers=user_agent, timeout=20)

                    with open(
                        "/Users/baekkwanghyun/Desktop/Projects/5.Viral/results/images/"
                        + img_name,
                        "wb",
                    ) as f:
                        f.write(response.content)

                    saved_imgs.add(img_name)

                time.sleep(0.5)

            print(f"총 {len(saved_imgs)} 장의 이미지 저장")
            data.append(str(list(saved_imgs)))

            Data_List.append(data)
            time.sleep(5)

        except Exception as e:
            print(e)
            print("오류 발생")
            patient += 1

            if patient > 3:
                break

        if idx != 0 and idx % 10 == 0:
            Data_List_New = []
            for data in Data_List:
                if data not in Data_List_New:
                    Data_List_New.append(data)

            print("-------------------------------------")
            print("{} 개의 데이터 크롤링 완료".format(len(Data_List_New)))
            df_Sheet = pd.DataFrame(
                Data_List_New,
                columns=[
                    "brand",
                    "username",
                    "date",
                    "post_url",
                    "full_text",
                    "like",
                    "saved_imgs",
                ],
            )
            df = pd.read_csv(
                results,
                encoding="utf-8",
                usecols=[
                    "brand",
                    "username",
                    "date",
                    "post_url",
                    "full_text",
                    "like",
                    "saved_imgs",
                ],
            )
            file = [df, df_Sheet]
            new_df = pd.concat(file, axis=0)
            final_df = new_df.drop_duplicates(
                subset=None, keep="first", inplace=False, ignore_index=True
            )
            final_df.to_csv(results, index=False, encoding="utf-8")

            Data_List.clear()
            time.sleep(10)

    driver.close()

    Data_List_New = []
    for data in Data_List:
        if data not in Data_List_New:
            Data_List_New.append(data)

    print("-------------------------------------")
    print("총 {} 개의 데이터 크롤링 완료".format(len(Data_List_New)))
    df_Sheet = pd.DataFrame(
        Data_List_New,
        columns=[
            "brand",
            "username",
            "date",
            "post_url",
            "full_text",
            "like",
            "saved_imgs",
        ],
    )
    df = pd.read_csv(
        results,
        encoding="utf-8",
        usecols=[
            "brand",
            "username",
            "date",
            "post_url",
            "full_text",
            "like",
            "saved_imgs",
        ],
    )
    file = [df, df_Sheet]
    new_df = pd.concat(file, axis=0)
    final_df = new_df.drop_duplicates(
        subset=None, keep="first", inplace=False, ignore_index=True
    )
    final_df.to_csv(results, index=False, encoding="utf-8")


if __name__ == "__main__":
    main()
