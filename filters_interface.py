import os
import tkinter as tk
from tkcalendar import DateEntry
import ctypes
import json
from ttkwidgets.autocomplete import AutocompleteCombobox
from PIL import Image, ImageTk
import platform

# Diretório base do script
script_dir = os.path.dirname(os.path.abspath(__file__))

class Item:
    def __init__(self, master, original_name, display_name, allow_images, deny_images, row):
        self.original_name = original_name
        self.display_name = display_name
        self.allow_state = False
        self.deny_state = False

        self.allow_empty, self.allow_checked = allow_images
        self.deny_empty, self.deny_checked = deny_images

        self.label = tk.Label(master, text=self.display_name)
        self.label.grid(row=row, column=0, padx=5, pady=2, sticky='w')
        
        self.lbl_allow = tk.Label(master, image=self.allow_empty)
        self.lbl_allow.grid(row=row, column=1, padx=5, pady=2, sticky='w')
        self.lbl_allow.bind("<Button-1>", self.click_allow)
        
        self.lbl_deny = tk.Label(master, image=self.deny_empty)
        self.lbl_deny.grid(row=row, column=2, padx=5, pady=2, sticky='w')
        self.lbl_deny.bind("<Button-1>", self.click_deny)
        
    def click_allow(self, event):
        if not self.allow_state:
            self.lbl_allow.config(image=self.allow_checked)
            self.lbl_deny.config(image=self.deny_empty)
            self.allow_state = True
            self.deny_state = False
        else:
            self.lbl_allow.config(image=self.allow_empty)
            self.allow_state = False

    def click_deny(self, event):
        if not self.deny_state:
            self.lbl_deny.config(image=self.deny_checked)
            self.lbl_allow.config(image=self.allow_empty)
            self.deny_state = True
            self.allow_state = False

class App:
    def __init__(self, root, callback):
        self.root = root
        self.callback = callback
        self.root.title("Busca de imagens")

        if platform.system() == "Windows":
            myappid = 'mycompany.myproduct.subproduct.version'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            self.root.iconbitmap(os.path.join(script_dir, "icons", "mks.ico"))
        else:
            img = Image.open(os.path.join(script_dir, "icons", "mks.png"))
            photo = ImageTk.PhotoImage(img)
            self.root.iconphoto(True, photo)

        self.root.resizable(False, False)
        
        self.allow_images = [tk.PhotoImage(file=os.path.join(script_dir, "icons", "allow_empty.png")), tk.PhotoImage(file=os.path.join(script_dir, "icons", "allow_checked.png"))]
        self.deny_images = [tk.PhotoImage(file=os.path.join(script_dir, "icons", "deny_empty.png")), tk.PhotoImage(file=os.path.join(script_dir, "icons", "deny_checked.png"))]
        
        self.items = []
        
        names = {
            'anemometro':   'Anemômetro:',
            'bussola':      'Bússola:',
            'carro':        'Carro:',
            'fundacao':     'Fundação:',
            'numero-serie': 'Número de Série:',
            'painel-carro': 'Painel de Carro:',
            'windvane':     'Windvane:'
        }
        
        self.items_frame = tk.Frame(self.root)
        self.items_frame.pack(fill=tk.X, padx=5, pady=5)
        
        row = 0
        for original_name, display_name in names.items():
            self.items.append(Item(self.items_frame, original_name, display_name, self.allow_images, self.deny_images, row))
            row += 1
        
        # Frame principal para Data de Upload
        self.date_frame = tk.Frame(self.root)
        self.date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Sub-frame para o título "Data de Upload"
        self.upload_label_frame = tk.Frame(self.date_frame)
        self.upload_label_frame.grid(row=0, column=0, sticky='w')
        
        tk.Label(self.upload_label_frame, text="Data de Upload: ").pack(anchor='w')
        
        # Sub-frame para os DateEntry
        self.upload_entry_frame = tk.Frame(self.date_frame)
        self.upload_entry_frame.grid(row=0, column=1, sticky='w')
        
        self.upload_start_date = DateEntry(self.upload_entry_frame, date_pattern='dd/mm/yyyy')
        self.upload_start_date.grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.upload_entry_frame, text="até").grid(row=0, column=1, padx=5, pady=5)
        self.upload_end_date = DateEntry(self.upload_entry_frame, date_pattern='dd/mm/yyyy')
        self.upload_end_date.grid(row=0, column=2, padx=5, pady=5)
        
        # Frame principal para Data Original
        self.original_date_frame = tk.Frame(self.root)
        self.original_date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Sub-frame para o título "Data Original"
        self.original_label_frame = tk.Frame(self.original_date_frame)
        self.original_label_frame.grid(row=0, column=0, sticky='w')
        
        tk.Label(self.original_label_frame, text="Data Original:    ").pack(anchor='w')
        
        # Sub-frame para os DateEntry
        self.original_entry_frame = tk.Frame(self.original_date_frame)
        self.original_entry_frame.grid(row=0, column=1, sticky='w')
        
        self.original_start_date = DateEntry(self.original_entry_frame, date_pattern='dd/mm/yyyy')
        self.original_start_date.grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.original_entry_frame, text="até").grid(row=0, column=1, padx=5, pady=5)
        self.original_end_date = DateEntry(self.original_entry_frame, date_pattern='dd/mm/yyyy')
        self.original_end_date.grid(row=0, column=2, padx=5, pady=5)

        self.no_original_date_var = tk.BooleanVar()
        self.no_original_date_checkbox = tk.Checkbutton(
            self.original_date_frame, text="Apenas imagens sem a data.", variable=self.no_original_date_var, command=self.toggle_original_date)
        self.no_original_date_checkbox.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='w')


        # Carrega todos os dados do JSON
        self.all_data = self.load_json_data()

        # Filtra as opções iniciais
        clientes = self.get_unique_values(self.all_data, 'client_name')
        self.client_frame = tk.Frame(self.root)
        self.client_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(self.client_frame, text="Nome do Cliente:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.client_name = AutocompleteCombobox(self.client_frame, completevalues=clientes)
        self.client_name.set = self.client_name
        self.client_name.grid(row=0, column=1, padx=5, pady=5, sticky='e')
        self.client_name.bind("<FocusOut>", self.update_tower_and_os_options)

        torres = self.get_unique_values(self.all_data, 'tower_name')
        self.tower_frame = tk.Frame(self.root)
        self.tower_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(self.tower_frame, text="Nome da Torre:  ").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.tower_name = AutocompleteCombobox(self.tower_frame, completevalues=torres)
        self.tower_name.set = self.tower_name
        self.tower_name.grid(row=0, column=1, padx=5, pady=5, sticky='e')
        self.tower_name.bind("<FocusOut>", self.update_client_and_os_options)

        os_nums = self.get_unique_values(self.all_data, 'os_number')
        self.os_frame = tk.Frame(self.root)
        self.os_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(self.os_frame, text="Número da OS:   ").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.os_number = AutocompleteCombobox(self.os_frame, completevalues=os_nums)
        self.os_number.grid(row=0, column=1, padx=5, pady=5, sticky='e')
        self.os_number.bind("<FocusOut>", self.update_client_and_tower_options)
        
        self.button = tk.Button(self.root, text='Buscar imagens', command=self.submit)
        self.button.pack(padx=5, pady=5)
    
    def load_json_data(self):
        directory = os.path.join(script_dir, 'images')
        all_data = []
        
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                filepath = os.path.join(directory, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        all_data.append(data)
                    except json.JSONDecodeError:
                        continue
        
        return all_data

    def get_unique_values(self, data, key):
        return list(set([item.get(key, "") for item in data if key in item]))

    def update_tower_and_os_options(self, event=None):
        selected_client = self.client_name.get()
        filtered_data = [item for item in self.all_data if item['client_name'] == selected_client or not selected_client]

        towers = self.get_unique_values(filtered_data, 'tower_name')
        self.tower_name.set_completion_list(towers)
        
        os_numbers = self.get_unique_values(filtered_data, 'os_number')
        self.os_number.set_completion_list(os_numbers)

    def update_client_and_os_options(self, event=None):
        selected_tower = self.tower_name.get()
        filtered_data = [item for item in self.all_data if item['tower_name'] == selected_tower or not selected_tower]

        clients = self.get_unique_values(filtered_data, 'client_name')
        self.client_name.set_completion_list(clients)
        
        os_numbers = self.get_unique_values(filtered_data, 'os_number')
        self.os_number.set_completion_list(os_numbers)

    def update_client_and_tower_options(self, event=None):
        selected_os = self.os_number.get()
        filtered_data = [item for item in self.all_data if item['os_number'] == selected_os or not selected_os]

        clients = self.get_unique_values(filtered_data, 'client_name')
        self.client_name.set_completion_list(clients)
        
        towers = self.get_unique_values(filtered_data, 'tower_name')
        self.tower_name.set_completion_list(towers)

    def toggle_original_date(self):
        state = 'disabled' if self.no_original_date_var.get() else 'normal'
        self.original_start_date.config(state=state)
        self.original_end_date.config(state=state)

    def submit(self):
        whitelist = []
        blacklist = []
        for item in self.items:
            if item.allow_state:
                whitelist.append(item.original_name)
            elif item.deny_state:
                blacklist.append(item.original_name)
        
        upload_period = f"{self.upload_start_date.get()}-{self.upload_end_date.get()}"
        original_period = "unknown" if self.no_original_date_var.get() else f"{self.original_start_date.get()}-{self.original_end_date.get()}"
        client_name = self.client_name.get()
        tower_name = self.tower_name.get()
        os_number = self.os_number.get()
        
        results = {
            "whitelist": whitelist,
            "blacklist": blacklist,
            "upload_period": upload_period,
            "original_period": original_period,
            "client_name": client_name,
            "tower_name": tower_name,
            "os_number": os_number
        }
    
        self.callback(results)

def show_filters_interface(callback):
    root = tk.Tk()
    app = App(root, callback)
    root.mainloop()
