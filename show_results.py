import os
import json
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox
from PIL import Image, ImageTk
from zipfile import ZipFile

# Definir a quantidade de imagens por página
IMAGES_PER_PAGE = 50

# Diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))

class ImageViewerApp:
    def __init__(self, root, json_filenames):
        self.root = root
        self.json_filenames = json_filenames
        self.current_page = 0  # Página inicial
        self.image_labels = []

        self.setup_ui()

    def setup_ui(self):
        self.root.geometry("700x600")
        self.root.title("Imagens Encontradas")

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=1)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        self.image_count_label = ttk.Label(top_frame, text=f"Total Images: {len(self.json_filenames)}")
        self.image_count_label.pack(side=tk.LEFT)

        download_button = ttk.Button(top_frame, text="Baixar todas", command=self.create_zip)
        download_button.pack(side=tk.RIGHT)

        delete_all_button = ttk.Button(top_frame, text="Apagar todas", command=self.delete_all_images)
        delete_all_button.pack(side=tk.RIGHT, padx=5)

        self.canvas = tk.Canvas(main_frame)
        self.scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        pagination_frame = ttk.Frame(self.root)
        pagination_frame.pack(fill=tk.X, pady=10)

        self.prev_button = ttk.Button(pagination_frame, text="<< Anterior", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.next_button = ttk.Button(pagination_frame, text="Próximo >>", command=self.next_page)
        self.next_button.pack(side=tk.RIGHT, padx=5)

        self.root.bind('<Configure>', self.update_grid)

        # Carregar a primeira página
        self.load_page(self.current_page)

    def delete_all_images(self):
        confirm = messagebox.askyesno("Confirmar Exclusão", "Deseja realmente excluir todas as imagens?")
        if confirm:
            try:
                for json_filename in self.json_filenames:
                    img_path = self.find_image_path(json_filename)
                    if img_path:
                        os.remove(img_path)
                    os.remove(os.path.join(script_dir, "images", json_filename))
                self.json_filenames.clear()
                self.load_page(0)
                messagebox.showinfo("Exclusão Concluída", "Todas as imagens foram excluídas com sucesso.")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível excluir todas as imagens: {e}")

    def create_zip(self):
        zip_filename = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        if not zip_filename:
            return

        try:
            with ZipFile(zip_filename, 'w') as zipf:
                for json_filename in self.json_filenames:
                    img_path = self.find_image_path(json_filename)
                    if img_path:
                        zipf.write(img_path, os.path.basename(img_path))
            messagebox.showinfo("Download Concluído", f"{zip_filename} foi criado com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível criar um arquivo zip: {e}")

    def update_grid(self, event=None):
        width = self.root.winfo_width()
        column_width = 210  # Largura da imagem + margem
        num_columns = max(1, (width - 10) // column_width)

        for idx, label in enumerate(self.image_labels):
            row = idx // num_columns
            column = idx % num_columns
            label.grid(row=row, column=column, padx=10, pady=10)

    def show_image_info(self, image_info, img_path):
        info_window = tk.Toplevel(self.root)
        info_window.title("Detalhes da Imagem")
        info_window.minsize(600, 400)

        canvas = tk.Canvas(info_window)
        scrollbar = ttk.Scrollbar(info_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        pil_img = Image.open(img_path)
        max_width, max_height = 300, 300
        pil_img.thumbnail((max_width, max_height))
        img_tk = ImageTk.PhotoImage(pil_img, master=info_window)
        img_label = ttk.Label(scrollable_frame, image=img_tk)
        img_label.image = img_tk
        img_label.pack(pady=10)

        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, pady=10)

        def download_image():
            save_path = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg"), ("All files", "*.*")]
            )
            if save_path:
                pil_img.save(save_path)
                messagebox.showinfo("Download Concluído", f"A imagem foi salva em {save_path}.")

        def delete_image():
            confirm = messagebox.askyesno("Confirmar Exclusão", "Deseja realmente excluir esta imagem?")
            if confirm:
                try:
                    os.remove(img_path)
                    os.remove(os.path.join(script_dir, "images", image_info['new_filename'].split('.')[0] + '.json'))
                except Exception as e:
                    messagebox.showerror("Erro", f"Não foi possível excluir a imagem: {e}")
                    return

                self.json_filenames.remove(image_info['new_filename'].split('.')[0] + '.json')
                info_window.destroy()
                self.load_page(self.current_page)
                messagebox.showinfo("Exclusão Concluída", "A imagem foi excluída com sucesso.")

        download_button = ttk.Button(button_frame, text="Download", command=download_image)
        download_button.pack(side=tk.LEFT, padx=5)

        delete_button = ttk.Button(button_frame, text="Apagar", command=delete_image)
        delete_button.pack(side=tk.LEFT, padx=5)

        basic_info = f"Original File: {image_info.get('original_file')}\n" \
                     f"New Filename: {image_info.get('new_filename')}\n" \
                     f"Original Folder: {image_info.get('original_folder')}\n" \
                     f"Upload Date: {image_info.get('upload_date')}\n" \
                     f"Original Date: {image_info.get('original_date')}\n" \
                     f"Client Name: {image_info.get('client_name')}\n" \
                     f"Tower Name: {image_info.get('tower_name')}\n" \
                     f"OS Number: {image_info.get('os_number')}\n"
        ttk.Label(scrollable_frame, text=basic_info, anchor='w', justify='left').pack(anchor='w', pady=10)

        objects_frame = ttk.LabelFrame(scrollable_frame, text="Objetos Encontrados")
        objects_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        if 'found_objects' in image_info and image_info.get('found_objects') != 'unknown':
            for obj in image_info.get('found_objects', []):
                if 'odometer' in obj:
                    obj_info =  f"Nome: {obj.get('name')}\n" \
                                f"Posição: {obj.get('position')}\n" \
                                f"Confidence: {obj.get('confidence')}\n" \
                                f"Odômetro: {obj.get('odometer')}\n"
                elif 'serial_number' in obj:
                    obj_info =  f"Nome: {obj.get('name')}\n" \
                                f"Posição: {obj.get('position')}\n" \
                                f"Confidence: {obj.get('confidence')}\n" \
                                f"Número de Série: {obj.get('serial_number')}\n"
                else:
                    obj_info =  f"Nome: {obj.get('name')}\n" \
                                f"Posição: {obj.get('position')}\n" \
                                f"Confidence: {obj.get('confidence')}\n"
                ttk.Label(objects_frame, text=obj_info, anchor='w', justify='left').pack(anchor='w', pady=5)
        else:
            ttk.Label(objects_frame, text="Nenhum objeto encontrado", anchor='w', justify='left').pack(anchor='w', pady=5)

    def on_image_click(self, img_info):
        json_path = os.path.join(script_dir, "images", img_info['json_filename'])
        img_path = self.find_image_path(img_info['json_filename'])
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                image_info = json.load(f)
            self.show_image_info(image_info, img_path)
        else:
            messagebox.showerror("Erro", f"Informações não encontradas para {img_info['json_filename']}")

    def find_image_path(self, json_filename):
        json_path = os.path.join(script_dir, "images", json_filename)
        
        if not os.path.exists(json_path):
            return None
        
        # Carrega o JSON e extrai o 'new_filename'
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            new_filename = data.get("new_filename")
        if not new_filename:
            return None
        
        # Constrói o caminho completo da imagem
        img_path = os.path.join(script_dir, "images", new_filename)
        
        if os.path.exists(img_path):
            return img_path
        
        return None

    def load_page(self, page):
        start_idx = page * IMAGES_PER_PAGE
        end_idx = start_idx + IMAGES_PER_PAGE
        displayed_filenames = self.json_filenames[start_idx:end_idx]

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.image_labels = []
        for json_filename in displayed_filenames:
            img_path = self.find_image_path(json_filename)
            if img_path:
                try:
                    pil_img = Image.open(img_path)
                    pil_img.thumbnail((200, 200))
                    img_tk = ImageTk.PhotoImage(pil_img, master=self.root)
                    label = ttk.Label(self.scrollable_frame, image=img_tk)
                    label.image = img_tk
                    img_info = {'json_filename': json_filename}
                    label.bind("<Button-1>", lambda e, img_info=img_info: self.on_image_click(img_info))
                    self.image_labels.append(label)
                    label.grid_configure()
                except Exception as e:
                    print(f"Erro ao carregar a imagem {img_path}: {e}")

        self.update_grid()

    def next_page(self):
        if (self.current_page + 1) * IMAGES_PER_PAGE < len(self.json_filenames):
            self.current_page += 1
            self.load_page(self.current_page)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page(self.current_page)

def show_results(json_filenames):
    root = tk.Tk()
    app = ImageViewerApp(root, json_filenames)
    root.mainloop()
