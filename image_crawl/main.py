import argparse
import json
from crawler import Crawler


def main():
    parser = argparse.ArgumentParser(description="Web Image Crawler")
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument(
        "--pages", type=int, default=10, help="Number of pages to crawl"
    )
    parser.add_argument(
        "--save_dir", type=str, required=True, help="Directory to save images"
    )

    args = parser.parse_args()

    # config.json
    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    urls = config["urls"]
    keywords = config["keywords"]
    headers = config["headers"]

    for url in urls:
        for keyword in keywords:
            print(f"Start crawling: {url} for keyword '{keyword}'")
            crawler = Crawler(
                base_url=url, headers=headers, save_directory=args.save_dir
            )
            crawler.crawl_page(keyword=keyword, pages=args.pages)


if __name__ == "__main__":
    main()
