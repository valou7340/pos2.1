import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable

class MenuPanel(tk.Frame):
    def __init__(self, parent, menu_data: Dict[str, Any], add_callback: Callable):
        super().__init__(parent, bg="#ffffff", bd=1, relief=tk.RAISED)
        self.menu_data = menu_data
        self.add_callback = add_callback
        self.create_widgets()
    
    def create_widgets(self):
        # Notebook pour les catégories
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Créer un onglet pour chaque catégorie
        for category, category_data in self.menu_data.items():
            frame = tk.Frame(self.notebook, bg="#f8f9fa")
            self.notebook.add(frame, text=category)
            
            # Scrollbar
            scrollbar = tk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Canvas pour le défilement
            canvas = tk.Canvas(frame, yscrollcommand=scrollbar.set, bg="#f8f9fa")
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=canvas.yview)
            
            # Frame interne pour les boutons
            inner_frame = tk.Frame(canvas, bg="#f8f9fa")
            canvas.create_window((0, 0), window=inner_frame, anchor="nw")
            
            # Boutons pour chaque item
            row, col = 0, 0
            for item_name, price in category_data["items"].items():
                btn_text = f"{item_name}\n{price:.2f}€"
                btn = tk.Button(
                    inner_frame, 
                    text=btn_text, 
                    width=15, 
                    height=3,
                    font=("Arial", 10),
                    bg="#3498db",
                    fg="white",
                    cursor="hand2",
                    command=lambda n=item_name, p=price, 
                           t=category_data["tva_rate"], 
                           c=category_data["category"]: self.add_callback(n, p, t, c)
                )
                btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                
                col += 1
                if col > 2:  # 3 colonnes par ligne
                    col = 0
                    row += 1
            
            # Configurer le canvas pour le défilement
            inner_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))
            
            # Bind la molette de la souris
            canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    
    def update_menu(self, new_menu_data: Dict[str, Any]):
        self.menu_data = new_menu_data
        # Recréer les widgets avec le nouveau menu
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()
