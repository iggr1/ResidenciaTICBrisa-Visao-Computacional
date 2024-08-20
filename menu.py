import ctypes
import platform
import tkinter as tk
from PIL import Image, ImageTk
import subprocess
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

def run_upload_images():
    subprocess.run(["python3", os.path.join(script_dir, "upload_images.py")])
    root.destroy()

def run_find_run():
    subprocess.run(["python3", os.path.join(script_dir, "find_run.py")])
    root.destroy()

# Criação da janela principal
root = tk.Tk()
root.geometry("350x250")
root.title("Anemovision Menu")

if platform.system() == "Windows":
    myappid = 'mycompany.myproduct.subproduct.version'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    root.iconbitmap(os.path.join(script_dir, "icons/mks.ico"))
else:
    img = Image.open(os.path.join(script_dir, "icons/mks.png"))
    photo = ImageTk.PhotoImage(img)
    root.iconphoto(True, photo)
    
root.resizable(False, False)

# Função para carregar e redimensionar a imagem
def load_image(path, size):
    image = Image.open(path)
    image = image.resize(size)
    return ImageTk.PhotoImage(image)

# Carregar e redimensionar as imagens
upload_img = load_image(os.path.join(script_dir, "icons/upload_icon.png"), (50, 50))  # Ajuste o tamanho conforme necessário
find_img = load_image(os.path.join(script_dir, "icons/find_icon.png"), (50, 50))      # Ajuste o tamanho conforme necessário

# Exibir a imagem acima do botão "Carregar Pastas"
upload_label = tk.Label(root, image=upload_img)
upload_label.pack(pady=(20, 0))  # Espaçamento no eixo y

# Botão para carregar pastas
upload_button = tk.Button(root, text="Carregar Pastas", command=run_upload_images)
upload_button.pack(pady=(0, 20))  # Espaçamento no eixo y

# Exibir a imagem acima do botão "Ver / Buscar Imagens"
find_label = tk.Label(root, image=find_img)
find_label.pack(pady=(20, 0))  # Espaçamento no eixo y

# Botão para ver/buscar imagens
find_button = tk.Button(root, text="Ver / Buscar Imagens", command=run_find_run)
find_button.pack(pady=(0, 20))  # Espaçamento no eixo y

# Inicia o loop principal do Tkinter
root.mainloop()
