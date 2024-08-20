import tkinter as tk
from tkinter import filedialog, messagebox
import shutil
import os
import subprocess
import threading
from PIL import Image, ImageTk 
import platform
import ctypes

# Lista para armazenar as pastas selecionadas
selected_folders = []
script_dir = os.path.dirname(os.path.abspath(__file__))

def add_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_name = os.path.basename(folder)
        if folder not in selected_folders:
            selected_folders.append(folder)
            listbox_folders.insert(tk.END, folder_name)

def send_folders():
    if not selected_folders:
        messagebox.showwarning("Aviso", "Nenhuma pasta foi selecionada.")
        return
    
    destination = os.path.join(script_dir, "upload")
    
    for folder in selected_folders:
        folder_name = os.path.basename(folder)
        dest_path = os.path.join(destination, folder_name)
        shutil.copytree(folder, dest_path)
    
    selected_folders.clear()
    listbox_folders.delete(0, tk.END)
    root.destroy()
    open_processing_window()

def open_processing_window():
    proc_window = tk.Tk()
    proc_window.title("Envio de pastas")

    if platform.system() == "Windows":
        myappid = 'mycompany.myproduct.subproduct.version'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        proc_window.iconbitmap(os.path.join(script_dir, "icons/mks.ico"))
    else:
        img = Image.open(os.path.join(script_dir, "icons/mks.png"))
        photo = ImageTk.PhotoImage(img)
        proc_window.iconphoto(True, photo)
    
    proc_window.resizable(False, False)
    label = tk.Label(proc_window, text="Aguarde o início do processamento (isso pode levar alguns segundos)...", font=("Arial", 12))
    label.pack(pady=10)

    text_output = tk.Text(proc_window, height=20, width=80)
    text_output.pack(pady=10, padx=10)

    def run_script():
        process = subprocess.Popen(("python", os.path.join(script_dir, "images_processing.py")), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        for line in process.stdout:
            text_output.insert(tk.END, line)
            text_output.see(tk.END)

        process.stdout.close()
        process.wait()

        messagebox.showinfo("Concluído", "O processamento das imagens foi concluído.")

    thread = threading.Thread(target=run_script)
    thread.start()

    proc_window.mainloop()

def remove_folder():
    selected = listbox_folders.curselection()
    if selected:
        index = selected[0]
        listbox_folders.delete(index)
        selected_folders.pop(index)

def main():
    global listbox_folders
    global root
    
    root = tk.Tk()
    root.title("Upload de Pastas")

    if platform.system() == "Windows":
        myappid = 'mycompany.myproduct.subproduct.version'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        root.iconbitmap(os.path.join(script_dir, "icons/mks.ico"))
    else:
        img = Image.open(os.path.join(script_dir, "icons/mks.png"))
        photo = ImageTk.PhotoImage(img)
        root.iconphoto(True, photo)

    root.resizable(False, False)

    add_button = tk.Button(root, text="Carregar Nova Pasta", command=add_folder)
    add_button.pack(pady=10)

    listbox_folders = tk.Listbox(root, width=50, height=10)
    listbox_folders.pack(pady=5)

    remove_button = tk.Button(root, text="Remover Pasta Selecionada", command=remove_folder)
    remove_button.pack(pady=5)

    send_button = tk.Button(root, text="Enviar Pastas", command=send_folders)
    send_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
