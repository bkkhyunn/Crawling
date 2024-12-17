import time
import random
import json

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
import threading


def load_config(path):
    """
    keywords 와 user-agent 가져오기

    Args:
        path (str): config 파일 경로

    Returns:
        keywords: crawling 검색 키워드
        user_agent: ip 차단 방지용 user-agent
    """

    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    keywords = config["keywords"]
    user_agent = config["headers"]["user-agent"]

    return keywords, user_agent


def scroll(driver):
    """
    스크롤을 끝까지 내리는 함수

    Args:
        driver (selenium.webdriver.chrome.webdriver.WebDriver): selenium 웹 드라이버

    Returns:
        None
    """
    try:
        # 페이지 내 스크롤 높이 받아오기
        last_page_height = driver.execute_script(
            "return document.documentElement.scrollHeight"
        )

        while True:
            # 임의의 페이지 로딩 시간 설정, 환경에 따라 로딩시간 최적화를 통해 scraping 시간 단축 가능
            pause_time = random.uniform(1, 2)

            # 페이지 최하단까지 스크롤
            driver.execute_script(
                "window.scrollTo(0, document.documentElement.scrollHeight);"
            )

            # 페이지 로딩 대기
            time.sleep(pause_time)

            # 무한 스크롤 동작을 위해 살짝 위로 스크롤(i.e., 페이지를 위로 올렸다가 내리는 제스쳐)
            driver.execute_script(
                "window.scrollTo(0, document.documentElement.scrollHeight-50)"
            )
            time.sleep(pause_time)

            # 페이지 내 스크롤 높이 새롭게 받아오기
            new_page_height = driver.execute_script(
                "return document.documentElement.scrollHeight"
            )

            # 스크롤을 완료한 경우(더이상 페이지 높이 변화가 없는 경우)
            if new_page_height == last_page_height:
                print("스크롤 완료")
                break

            # 스크롤 완료하지 않은 경우, 최하단까지 스크롤
            else:
                last_page_height = new_page_height

    except Exception as e:
        print("에러 발생: ", e)


def start_driver(user_agent, timeout=15):
    """
    Selenium WebDriver 실행, 지정한 시간 내에 실행되지 않으면 TimeoutError 를 발생

    Args:
        args (argparse): config 얻기
        timeout (int): 타임아웃 시간(초).

    Returns:
        webdriver: Selenium WebDriver 객체

    Raises:
        TimeoutError: 드라이버가 타임아웃 내에 실행되지 않으면 발생
    """
    driver = None
    error = None
    user_agent = user_agent

    def launch_driver():
        nonlocal driver, error
        try:
            service = Service()
            options = webdriver.ChromeOptions()
            options.add_argument("user-agent=" + user_agent)
            options.add_argument("headless")
            options.add_argument("--mute-audio")
            options.add_argument("--disable-gpu")
            options.add_argument("--no_sandbox")
            options.add_argument(
                "--disable-extensions"
            )  # Chrome 확장 프로그램 비활성화
            options.add_argument(
                "--disable-dev-shm-usage"
            )  # Chrome 이 /dev/shm(공유 메모리) 사용 비활성화
            options.add_argument(
                "--disable-blink-features=AutomationControlled"
            )  # 웹 사이트에서 브라우저가 자동화 도구를 통해 제어되고 있음을 감지하지 못하도록
            options.add_argument("--incognito")  # 시크릿 모드
            options.add_argument(
                "--disable-infobars"
            )  # "Chrome이 자동화된 테스트 소프트웨어에 의해 제어되고 있습니다"라는 메시지 숨기기

            # options.add_argument("--proxy-server=http://proxy.example.com:8080") proxy 사용 예제
            # options.add_argument("--remote-debugging-port=0000") 원격 디버깅 포트 설정 예제

            driver = webdriver.Chrome(service=service, options=options)

        except WebDriverException as e:
            error = e

    # 스레드로 드라이버 실행
    thread = threading.Thread(target=launch_driver)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        # 타임아웃 발생 시 스레드를 중단하고 에러 발생
        raise TimeoutError(f"WebDriver did not start within {timeout} seconds.")

    if error:
        # WebDriverException 발생 시 다시 던짐
        raise error

    return driver
