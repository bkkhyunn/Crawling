import pandas as pd
import shutil
import os
from paddleocr import PaddleOCR
from tqdm import tqdm


def main():
    # OCR 엔진
    ocr = PaddleOCR(use_angle_cls=True, lang='korean', show_log=False)

    # 파일 경로
    data = '/Users/baekkwanghyun/Desktop/Projects/5.Viral/results/data.csv'    
    final = '/Users/baekkwanghyun/Desktop/Projects/5.Viral/results/final_data.csv'
    backup = '/Users/baekkwanghyun/Desktop/Projects/5.Viral/results/final_data_backup.csv'

    initial = False

    if os.path.exists(final):
        # 백업 파일
        shutil.copyfile(final, backup)
        final_df = pd.read_csv(final, encoding='utf-8', usecols=['brand', 'username', 'date', 'post_url', 'full_text', 'like', 'saved_imgs', 'ocr_text'])
        
    else:
        initial = True
        shutil.copyfile(data, final)
        final_df = pd.read_csv(final, encoding='utf-8', usecols=['brand', 'username', 'date', 'post_url', 'full_text', 'like', 'saved_imgs'])
        final_df['ocr_text'] = pd.NA
        final_df.to_csv(final, index=False, encoding='utf-8')

    # data.csv 에서 새로 생긴 데이터만 추출(최초에는 모두 ocr 을 돌려야 함)
    if not initial:
        data_df = pd.read_csv(data, encoding='utf-8', usecols=['brand', 'username', 'date', 'post_url', 'full_text', 'like', 'saved_imgs'])
        new_data_df = data_df.merge(final_df, on=['brand', 'username', 'date', 'post_url', 'full_text', 'like', 'saved_imgs'], how='left', indicator=True)
        new_data_df = new_data_df[new_data_df['_merge'] == 'left_only'].drop(columns=['_merge'])

        # OCR 컬럼 추가
        new_data_df['ocr_text'] = pd.NA

    else:
        new_data_df = final_df

    dir_path = '/Users/baekkwanghyun/Desktop/Projects/5.Viral/results/images/'

    # OCR 처리
    for i, img_paths in tqdm(new_data_df['saved_imgs'].items(), total=len(new_data_df)):
        img_paths = eval(img_paths)  # 문자열을 리스트로 변환
        
        if pd.notna(new_data_df.at[i, 'ocr_text']):
            continue
        
        ocr_texts = []
        for img_path in img_paths:
            full_img_path = dir_path + img_path
            try:
                result = ocr.ocr(full_img_path, cls=True)
                txts = [line[1][0] for line in result[0]]
                scores = [line[1][1] for line in result[0]]
                ocr_texts.extend(txt for txt, score in zip(txts, scores) if score > 0.9)
            except Exception:
                print(f"{full_img_path} 내 text 없음")
        
        ocr_text = ' '.join(ocr_texts)
        new_data_df.at[i, 'ocr_text'] = ocr_text

    # 데이터 합치기
    if not initial:
        final_df = pd.read_csv(final, encoding='utf-8', usecols=['brand', 'username', 'date', 'post_url', 'full_text', 'like', 'saved_imgs', 'ocr_text'])
        final_df = pd.concat([final_df, new_data_df], ignore_index=True)
    else:
        final_df = new_data_df

    final_df.to_csv(final, index=False, encoding='utf-8')


if __name__ == '__main__':
    main()