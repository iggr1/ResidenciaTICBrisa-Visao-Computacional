#!/usr/bin/env python3

import os
import shutil
import uuid
import json
import logging
from datetime import datetime
from threading import Lock
from scripts.get_object import get_objects
from scripts.get_date import get_date

# Configuração de variáveis globais
lock = Lock()
folders_to_process = set()

# Diretório base do script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configuração do logger
log_path = os.path.join(script_dir, "logs", "general.log")
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("images_processing")

# Função para adicionar todas as pastas da raiz "upload"
def initialize_processing():
    upload_root = os.path.join(script_dir, "upload")  # Caminho absoluto para a pasta de upload
    if os.path.exists(upload_root):
        for root, dirs, _ in os.walk(upload_root):
            for directory in dirs:
                folder_path = os.path.join(root, directory)
                first_two_folders = os.sep.join(folder_path.split(os.sep)[:4])  # Alterado para pegar corretamente a estrutura da pasta
                folders_to_process.add(first_two_folders)
        logger.info(f"Pastas encontradas para processamento: {folders_to_process}")
        process_folders()
    else:
        logger.error("Diretório de upload não encontrado")

# Função para processar as pastas
def process_folders():
    with lock:
        folders = list(folders_to_process)
        folders_to_process.clear()

    # Processar as pastas
    for folder in folders:
        if os.path.exists(folder):
            backup_folder(folder)
            logger.debug(f"Processando imagens de: {folder}")
            process_images_in_folder(folder)
            logger.info(f"Processamento de imagens finalizado em: {folder}")
            remove_folder(folder)

# Função para fazer backup de pastas
def backup_folder(folder_path):
    logger.debug(f"Iniciando backup de: {folder_path}")

    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg')

    # Verificar se a pasta tem imagens
    has_images = any(
        file.lower().endswith(image_extensions)
        for root, _, files in os.walk(folder_path)
        for file in files
    )
    
    print(f"Verificação de imagens: {has_images}")
    if not has_images:
        logger.debug(f"Nenhuma imagem encontrada em {folder_path}")
        return
    else:
        logger.debug(f"Imagens encontradas em {folder_path}")

    atual_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Criação do caminho de backup com a data
    backup_path = os.path.join(script_dir, "backup", atual_date)

    # Criação do backup
    if any(os.scandir(folder_path)):
        if not os.path.exists(backup_path):
            shutil.copytree(folder_path, backup_path)
            print(f"Backup criado: {backup_path}")
            logger.info(f"Backup criado: {backup_path}")
        else:
            logger.debug(f"Backup já existe: {backup_path}")
    else:
        print(f"Não há imagens para fazer backup em {folder_path}")
        logger.debug(f"Não há imagens para fazer backup em {folder_path}")

# Função para processar as imagens
def process_images_in_folder(folder_path):
    images_folder = os.path.join(script_dir, "images")
    os.makedirs(images_folder, exist_ok=True)

    # Andar por todas as pastas e arquivos
    for root, _, files in os.walk(folder_path):
        for item in files:
            original_img_path = os.path.join(root, item)

            # Verificar se o arquivo é uma imagem
            if is_image_file(original_img_path):
                print("\n------------------------------------------")
                print(f"\n-> Processando a pasta: {folder_path}")
                print(f"Processando {item} ({files.index(item) + 1}/{len(files)})")

                # Copiar a imagem para a pasta de imagens
                new_filename = create_filename(item)
                new_image_path = os.path.join(images_folder, new_filename)
                shutil.copy(original_img_path, new_image_path)

                # Obter informações dos objetos na imagem
                objects_info = get_objects(new_image_path)

                # Obter a data original da imagem
                original_date = get_date(new_image_path)

                # Verificar se a data foi obtida com sucesso
                if original_date and not (isinstance(original_date, dict) and "error" in original_date):
                    original_date = original_date.strftime("%d/%m/%Y %H:%M:%S")
                    print(f"\n-> Data que a foto foi tirada: {original_date}")
                else:
                    original_date = "unknown"
                    print("\n-> Data que a foto foi tirada: Desconhecida")

                # Obter informações do diretório
                directory_part = original_img_path.split(os.sep)

                # Informações para o arquivo JSON
                info_json = {
                    "original_file": os.path.basename(original_img_path),
                    "new_filename": new_filename,
                    "original_folder": os.path.dirname(original_img_path).replace("\\", "/"),
                    "upload_date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "original_date": original_date,
                    "client_name": directory_part[4],  # Ajustado para acessar corretamente
                    "tower_name": directory_part[5],
                    "os_number": directory_part[6],
                    "found_objects": objects_info
                }

                # Criação do arquivo JSON
                create_json(info_json, new_image_path)
            else:
                print(f"\n-> O arquivo {item} não é uma imagem. Continuando...")

# Função para verificar se o arquivo é uma imagem
def is_image_file(file_path):
    return os.path.isfile(file_path) and file_path.lower().endswith(
        ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg'))

# Função para criar um novo nome de arquivo
def create_filename(original_filename):
    random_id = uuid.uuid4().hex[:16]
    file_extension = os.path.splitext(original_filename)[1]
    return f"{random_id}{file_extension}"

# Função para criar um arquivo JSON
def create_json(metadata, img_path):
    json_filename = f"{os.path.splitext(os.path.basename(img_path))[0]}.json"
    json_path = os.path.join(os.path.dirname(img_path), json_filename)

    # Criação do arquivo JSON
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(metadata, json_file, ensure_ascii=False, indent=4)
    print(f"\n-> JSON criado: {json_path}")

# Função para remover pastas
def remove_folder(folder_path):
    shutil.rmtree(folder_path)
    print(f"-> Pasta Removida: {folder_path}")
    logger.info(f"Pasta removida: {folder_path}")

if __name__ == "__main__":
    initialize_processing()
