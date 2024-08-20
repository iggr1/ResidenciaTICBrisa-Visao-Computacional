import exifread
import os
from datetime import datetime
from scripts.get_date_ocr import process_image
import contextlib
import io
import logging

# Configuração do logger para evitar mensagens de ERRO em imagens PNG.
logging.getLogger('exifread').setLevel(logging.ERROR)

def get_image_metadata(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"O arquivo {image_path} não foi encontrado.")
    
    if image_path.lower().endswith(('jpg', 'jpeg')):
        with open(image_path, 'rb') as img_file:
            try:
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    tags = exifread.process_file(img_file)
                for tag in tags.keys():
                    if tag in ('EXIF DateTimeOriginal', 'EXIF DateTimeDigitized'):
                        date_string = str(tags[tag])
                        date_obj = datetime.strptime(date_string, "%Y:%m:%d %H:%M:%S")
                        return date_obj
            except:
                pass
    return None

# Função para obter a data da imagem
def get_date(img_path):
    date_obj = get_image_metadata(img_path)
    if date_obj:
        print('\nV - Data obtida dos metadados da imagem...')
        try:
            return date_obj
        except ValueError:
            pass
    else:
        print('\nX - Data não encontrada nos metadados da imagem. Utilizando OCR...')
        date_obj = process_image(img_path)
        return date_obj