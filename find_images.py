import os
import json
from datetime import datetime

# Diretório base do script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Caminho para a pasta de imagens
directory_path = os.path.join(script_dir, 'images')

def load_json_files(directory):
    json_files = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename), 'r') as file:
                json_object = json.load(file)
                json_object['filename'] = filename
                json_files.append(json_object)
    return json_files

def parse_date(date_str):
    if date_str.lower() == "unknown":
        return None
    try:
        return datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            return None

def date_in_range(date, start, end):
    if date is None:
        return False
    return start <= date <= end

def filter_images(images, filters):
    filtered_images = []
    for image in images:
        # Check client_name, tower_name, os_number
        if filters.get('client_name') and filters['client_name'] != image.get('client_name'):
            continue
        if filters.get('tower_name') and filters['tower_name'] != image.get('tower_name'):
            continue
        if filters.get('os_number') and filters['os_number'] != image.get('os_number'):
            continue
        
        # Check upload_period
        upload_date = parse_date(image.get('upload_date'))
        if filters.get('upload_period'):
            start_str, end_str = filters['upload_period'].split('-')
            start_date = parse_date(start_str)
            end_date = parse_date(end_str)
            end_date = end_date.replace(hour=23, minute=59, second=59)
            if not date_in_range(upload_date, start_date, end_date):
                continue

        # Check whitelist
        if filters.get('whitelist'):
            found_objects = image.get('found_objects', [])
            if isinstance(found_objects, str) and found_objects.lower() == "unknown":
                found_objects = []
            whitelist_match = all(any(obj['name'] == item for obj in found_objects) for item in filters['whitelist'])
            if not whitelist_match:
                continue

        # Check blacklist
        if filters.get('blacklist'):
            found_objects = image.get('found_objects', [])
            if isinstance(found_objects, str) and found_objects.lower() == "unknown":
                found_objects = []
            blacklist_match = any(obj['name'] in filters['blacklist'] for obj in found_objects)
            if blacklist_match:
                continue

        # Check original_period
        original_date = parse_date(image.get('original_date'))
        if filters.get('original_period'):
            if filters['original_period'] == "unknown":
                image_date = image["original_date"]
                if image_date.lower() == "unknown":
                    filtered_images.append(image)
                continue
            else:
                start_str, end_str = filters['original_period'].split('-')
                start_date = parse_date(start_str)
                end_date = parse_date(end_str)
                end_date = end_date.replace(hour=23, minute=59, second=59)
                if not date_in_range(original_date, start_date, end_date):
                    continue

        # If all checks passed, add to filtered list
        filtered_images.append(image)
    
    return filtered_images

def find_images(filters_object):
    images = load_json_files(directory_path)
    filtered_images = filter_images(images, filters_object)
    # Retornar apenas o nome dos arquivos
    return [image['filename'] for image in filtered_images]
