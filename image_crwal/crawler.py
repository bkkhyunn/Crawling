import os
import requests
from bs4 import BeautifulSoup
from utils import save_image


class Crawler:
    def __init__(self, base_url, headers, save_directory):
        self.base_url = base_url
        self.headers = headers
        self.save_directory = save_directory
        os.makedirs(save_directory, exist_ok=True)

    def crawl_page(self, keyword, pages=1):
        image_num = 1
        for page in range(1, pages + 1):
            params = {"q": keyword, "page": page}
            response = requests.get(self.base_url, headers=self.headers, params=params)
            if response.status_code != 200:
                print(
                    f"Failed to fetch page {page}. Status code: {response.status_code}"
                )
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            images = soup.find_all("img")

            for img in images:
                img_url = img.get("src")
                if img_url and img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif not img_url.startswith("http"):
                    continue
                save_path = os.path.join(self.save_directory, f"image_{image_num}.jpg")
                save_image(img_url, save_path)
                print(f"Saved: {save_path}")
                image_num += 1
