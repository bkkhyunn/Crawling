from datetime import datetime
import argparse
import os
from youtube_crawler import Youtube_Crawler


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        type=str,
        required=False,
        default="/Users/config.json",
    )
    parser.add_argument(
        "--period",
        type=str,
        required=False,
        default="week",
    )
    parser.add_argument(
        "--step",
        type=int,
        required=False,
        default=4,
    )
    parser.add_argument(
        "--data_path",
        type=str,
        required=False,
        default="/Users/data/",
    )
    parser.add_argument(
        "--date_op",
        type=str,
        required=False,
        default=False,
    )  # ex. "2024-11-01" <- 이와 같은 형태여야 한다.
    parser.add_argument(
        "--save_batch",
        type=int,
        required=False,
        default=1,
    )

    args = parser.parse_args()
    crawler = Youtube_Crawler(args)

    pre = os.path.join(args.data_path, "pre")
    post = os.path.join(args.data_path, "post")
    backup = os.path.join(args.data_path, "backup")
    # 폴더 없으면 생성
    for folder in [args.data_path, pre, post, backup]:
        if not os.path.exists(folder):
            os.mkdir(folder)
            print("data 폴더를 생성합니다.")

    if args.step == 1:
        crawler.search_crawling()

    elif args.step == 2:
        crawler.description_crawling()

    elif args.step == 3:
        crawler.update_data()
        c = datetime.now()
        print(f"{c} 데이터 최신화 끝", end="\n")

    else:
        c1 = datetime.now()
        print(f"{c1} 작업 시작", end="\n")
        crawler.search_crawling()
        crawler.description_crawling()
        crawler.update_data()
        c2 = datetime.now()
        print(f"{c2} 전체 끝", end="\n")
        elapsed_time = c2 - c1
        print(f"총 작업 시간: {elapsed_time}")
        print()


if __name__ == "__main__":
    main()
