from ultralytics import YOLO
import cv2
import os
import math
import numpy as np
import easyocr
import re
from datetime import datetime
import unicodedata

date_detector = YOLO('/root/Anemovision/models/DataFinder_light.pt')
reader_1 = easyocr.Reader(['en'])
reader_2 = easyocr.Reader(['pt'])

target_colors = [
    [255, 255, 255], # 0 rgb(255, 255, 255)
    [255, 255, 0  ], # 1 rgb(255, 255, 0)
    [255, 127, 0  ], # 2 rgb(255, 127, 20)
    [255, 0,   0  ], # 3 rgb(255, 0, 0)
    [0,   0,   0  ]  # 4 rgb(0, 0, 0)
]

def rgb_to_xyz(rgb):
    rgb = rgb / 255.0
    mask = rgb > 0.04045
    rgb[mask] = ((rgb[mask] + 0.055) / 1.055) ** 2.4
    rgb[~mask] = rgb[~mask] / 12.92
    rgb = rgb * 100

    transformation_matrix = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041]
    ])

    xyz = np.dot(rgb, transformation_matrix.T)
    
    return xyz

def xyz_to_lab(xyz):
    ref_white = np.array([95.047, 100.0, 108.883])
    xyz = xyz / ref_white
    mask = xyz > 0.008856
    xyz[mask] = np.cbrt(xyz[mask])
    xyz[~mask] = (7.787 * xyz[~mask]) + (16 / 116)
    
    l = (116 * xyz[..., 1]) - 16
    a = 500 * (xyz[..., 0] - xyz[..., 1])
    b = 200 * (xyz[..., 1] - xyz[..., 2])
    
    lab = np.stack([l, a, b], axis=-1)
    
    return lab

def rgb_to_lab(rgb):
    xyz = rgb_to_xyz(rgb)
    lab = xyz_to_lab(xyz)
    return lab

def color_distance(color1, color2):
    lab1 = rgb_to_lab(np.array(color1, dtype=np.float64))
    lab2 = rgb_to_lab(np.array(color2, dtype=np.float64).reshape(1, -1))
    return np.linalg.norm(lab1 - lab2, axis=1)

def get_box_aspect_ratio(width, height):
    max_dim = max(width, height)
    min_dim = min(width, height)
    return min_dim / max_dim

def get_box_score(aspect_ratio, confidence):
    return ((1 - aspect_ratio) + confidence) / 2

# def show_image(image, title='Image', footer_text=None):
#     return
    # plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    # plt.title(title)
    # if footer_text:
    #     plt.figtext(footer_text)
    # plt.axis('off')
    # plt.show()

def increase_visibility(img, target_color):
    img_float = img.astype(np.float64)
    pixels = img_float.reshape(-1, 3)
    distances = color_distance(pixels, target_color)
    distances_norm = (distances - distances.min()) / (distances.max() - distances.min())
    visibility_map = distances_norm * 255
    visibility_img = visibility_map.reshape(img.shape[:2])
    visibility_img = np.stack([visibility_img] * 3, axis=-1)
    return visibility_img.astype(np.uint8)

def parse_dates(input_string):
    parts = input_string.split()
    current_year = datetime.now().year
    current_date = datetime.now()
    valid_dates = []

    i = 0
    while i < len(parts) - 2:
        try:
            # Check for "dd mm yyyy" format
            day = int(parts[i])
            month = int(parts[i + 1])
            year = int(parts[i + 2])

            is_valid = 1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= current_year
            is_valid = is_valid and len(parts[i]) == 2 and len(parts[i + 1]) == 2 and len(parts[i + 2]) == 4
            
            if is_valid:
                date_str = f"{day:02d}/{month:02d}/{year}"
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                time_str = None
                if i + 4 < len(parts) and len(parts[i + 3]) == 2 and len(parts[i + 4]) == 2:
                    hour = int(parts[i + 3])
                    minute = int(parts[i + 4])
                    if 0 <= hour < 24 and 0 <= minute < 60:
                        time_str = f"{hour:02d}:{minute:02d}"
                        if i + 5 < len(parts) and len(parts[i + 5]) == 2:
                            second = int(parts[i + 5])
                            if 0 <= second < 60:
                                time_str += f":{second:02d}"
                if time_str:
                    date_time_str = f"{date_str} {time_str}"
                    date_obj = datetime.strptime(date_time_str, "%d/%m/%Y %H:%M:%S" if len(time_str) > 5 else "%d/%m/%Y %H:%M")
                valid_dates.append(date_obj)
            
            # Check for "yyyy-mm-dd" format
            year = int(parts[i])
            month = int(parts[i + 1])
            day = int(parts[i + 2])

            is_valid = 2000 <= year <= current_year and 1 <= month <= 12 and 1 <= day <= 31
            is_valid = is_valid and len(parts[i]) == 4 and len(parts[i + 1]) == 2 and len(parts[i + 2]) == 2
            
            if is_valid:
                date_str = f"{year}-{month:02d}-{day:02d}"
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                time_str = None
                if i + 4 < len(parts) and len(parts[i + 3]) == 2 and len(parts[i + 4]) == 2:
                    hour = int(parts[i + 3])
                    minute = int(parts[i + 4])
                    if 0 <= hour < 24 and 0 <= minute < 60:
                        time_str = f"{hour:02d}:{minute:02d}"
                        if i + 5 < len(parts) and len(parts[i + 5]) == 2:
                            second = int(parts[i + 5])
                            if 0 <= second < 60:
                                time_str += f":{second:02d}"
                if time_str:
                    date_time_str = f"{date_str} {time_str}"
                    date_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S" if len(time_str) > 5 else "%Y-%m-%d %H:%M")
                valid_dates.append(date_obj)
        
        except ValueError:
            pass

        i += 1

    valid_dates = [date for date in valid_dates if date <= current_date]
    if valid_dates:
        return max(valid_dates)
    else:
        return None

def replace_pattern_1(input_string):
    current_year = datetime.now().year
    
    def replace_match(match):
        y = int(match.group(1))
        r = match.group(2)
        if 2000 <= y <= current_year:
            return f"{y} {r}"
        else:
            return f"{y}{r}"
    
    pattern = re.compile(r'(\d{4})(\d+)')
    result = pattern.sub(replace_match, input_string)
    return result

def replace_pattern_2(input_string):
    current_year = datetime.now().year
    
    def replace_match(match):
        y = int(match.group(2))
        r = match.group(1)
        if 2000 <= y <= current_year:
            return f"{r} {y}"
        else:
            return f"{r}{y}"
    
    pattern = re.compile(r'(\d+)(\d{4})')
    result = pattern.sub(replace_match, input_string)
    return result

def replace_months(text):
    months = {
        "jan": "01",
        "fev": "02",
        "mar": "03",
        "abr": "04",
        "mai": "05",
        "jun": "06",
        "jul": "07",
        "ago": "08",
        "set": "09",
        "out": "10",
        "nov": "11",
        "dez": "12"
    }

    alphabet = "abcdefghijklmnopqrstuvwxyz"

    for letter in alphabet:
        for month in months:
            month_first_letter = month[0]
            if month_first_letter == letter:
                continue

            month_last_letter = month[-1]
            if month_last_letter == letter:
                continue
            
            regex_1 = re.compile(rf"{letter}{month[1:]}", re.IGNORECASE)
            regex_2 = re.compile(rf"{month[:-1]}{letter}", re.IGNORECASE)

            if regex_1.search(text):
                text = re.sub(regex_1, f"{month}", text)
            elif regex_2.search(text):
                text = re.sub(regex_2, f"{month}", text)

    def add_zero(match):
        num = match.group(1)
        month = match.group(2).lower()
        if len(month) > 3:
            month = month[:3]
        if not months.get(month):
            return match.group(0)
        num = num.zfill(2)
        return f"{num} {months[month]}"
    
    pattern = re.compile(r"(\d{1,2}) de (\w+)", re.IGNORECASE)
    result = re.sub(pattern, add_zero, text)
    
    return result

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def perform_date_ocr(img, reader):
    text = reader.readtext(img, paragraph=True)
    text = ' '.join([chunk[1] for chunk in text])

    text = remove_accents(text)
    common_mistakes = { 'O':'0', 'I':'1', 'l':'1', 'S':'5', 'B':'8' }
    for mistake, correction in common_mistakes.items():
        text = text.replace(mistake, correction)

    text = re.sub(r'([0-9])([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])([0-9])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])(de [0-9])', r'\1 \2', text)
    text = re.sub(' +', ' ', text).strip()
    text = replace_months(text)
    text = re.sub(r'[^0-9]', ' ', text)
    text = re.sub(' +', ' ', text).strip()

    for i in range(2):
        text = replace_pattern_1(text)
        text = replace_pattern_2(text)

    date = parse_dates(text)
    
    if date:
        return date
    
    return None

def extract_date(img):
    # show_image(img, "cropped Image")

    for i, color in enumerate(target_colors):

        new_img = increase_visibility(img, color)
        # show_image(new_img, f"color: {color}")

        date = perform_date_ocr(new_img, reader_1)
        if date:
            return date
        
        date = perform_date_ocr(new_img, reader_2)
        if date:
            return date

    return None

def process_image(img_path):
    try:
        img = cv2.imread(img_path
    )
        # show_image(img, "original image")
        detection = date_detector.predict(img, conf=0.5)
        boxes = []
        img_width = img.shape[1]
        img_height = img.shape[0]
        x_margin = int(img_width * 0.0075)
        y_margin = int(img_width * 0.0025)

        for det in detection:
            for box in det.boxes:
                x1, y1 = map(lambda x: math.floor(x.item()), box.xyxy[0][:2])
                x2, y2 = map(lambda x: math.ceil(x.item()), box.xyxy[0][2:])

                x1 = max(0, x1 - x_margin)
                y1 = max(0, y1 - y_margin)
                x2 = min(img_width, x2 + x_margin)
                y2 = min(img_height, y2 + y_margin)

                width = x2 - x1
                height = y2 - y1

                if width <= 0 or height <= 0:
                    continue

                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                aspect_ratio = get_box_aspect_ratio(width, height)
                score = get_box_score(aspect_ratio, confidence)

                boxes.append([x1, y1, x2, y2, confidence, class_id, width, height, aspect_ratio, score])

        total_boxes = len(boxes)

        if total_boxes == 0:
            check_result = check_image(img_path)
            if isinstance(check_result, dict) and "error" in check_result:
                return check_result
            return {"error": "no boxes found"}

        if total_boxes > 1:
            boxes = sorted(boxes, key=lambda box: box[7], reverse=True)

        result = None

        for box in boxes:
            x1, y1, x2, y2, confidence, class_id, width, height, aspect_ratio, score = box
            cropped_img = img[y1:y2, x1:x2]
            is_vertical = height > width

            if is_vertical:
                cropped_img = cv2.rotate(cropped_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

            date = extract_date(cropped_img)

            if date:
                result = date
                break

            rotated_img = cv2.rotate(cropped_img, cv2.ROTATE_180)

            date = extract_date(rotated_img)

            if date:
                result = date
                break

        if result:
            return result
        else:
            return {"error": "box found but no date detected."}
    except Exception as e:
        return {"error": "failed to process image"}

def check_image(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "image could not be read"}

        height, width, channels = img.shape
        if height == 0 or width == 0:
            return {"error": "image has invalid dimensions"}

        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        unique, counts = np.unique(gray_img, return_counts=True)
        color_counts = dict(zip(unique, counts))
        
        if color_counts.get(0, 0) / (height * width) > 0.25:
            return {"error": "image contains large black areas"}
    except Exception as e:
        return {"error": f"failed to process image"}

def process_folder(folder_path):
    if os.path.exists('output.txt'):
        os.remove('output.txt')

    files = os.listdir(folder_path)
    files.sort(key=lambda x: int(re.search(r'\d+', x).group()))

    total_processed = 0
    total_success = 0

    for file in files:
        file_path = os.path.join(folder_path, file)
        date = process_image(file_path)
        total_processed += 1
        with open('output.txt', 'a') as f:
            if isinstance(date, dict) and "error" in date:
                error = date['error']
                f.write(f"\n{file}: error: {error}")

                if ('large black areas' in error) or ('failed to process' in error):
                    total_processed -= 1
            else:
                total_success += 1
                f.write(f"\n{file}: {date}")