import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from app.services.order_service import OrderService

class OrderPanel(tk.Frame):
    def __init__(self, parent, order_service: OrderService, 
                 update_callback: Callable, remove_callback: Callable):
        super().__init__(parent, bg="#ffffff", bd=1, relief=tk.RAISED)
        self.order_service = order_service
        self.update_callback = update_callback
        self.remove_callback = remove_callback
        self.create_widgets()
        self.update_display()
    
    def create_widgets(self):
        # Titre
        title_label = tk.Label(self, text="📋 COMMANDE EN COURS", 
                              font=("Arial", 14, "bold"), bg="#ffffff")
        title_label.pack(pady=10)
        
        # Frame pour la liste des articles
        list_frame = tk.Frame(self, bg="#ffffff")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview pour afficher les articles
        columns = ("article", "quantité", "prix", "total")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        # Définir les colonnes
        self.tree.heading("article", text="Article")
        self.tree.heading("quantité", text="Quantité")
        self.tree.heading("prix", text="Prix Unitaire")
        self.tree.heading("total", text="Total")
        
        self.tree.column("article", width=200)
        self.tree.column("quantité", width=80, anchor="center")
        self.tree.column("prix", width=100, anchor="e")
        self.tree.column("total", width=100, anchor="e")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame pour les boutons d'action
        button_frame = tk.Frame(self, bg="#ffffff")
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Boutons
        tk.Button(button_frame, text="➕", font=("Arial", 12), width=3,
                 command=self.increment_quantity, bg="#27ae60", fg="white").pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="➖", font=("Arial", 12), width=3,
                 command=self.decrement_quantity, bg="#e74c3c", fg="white").pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="🗑️ Supprimer", font=("Arial", 10),
                 command=self.remove_item, bg="#95a5a6", fg="white").pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="🔄 Actualiser", font=("Arial", 10),
                 command=self.update_display, bg="#3498db", fg="white").pack(side=tk.RIGHT, padx=5)
    
    def update_display(self):
        # Vider le treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ajouter les articles
        for item in self.order_service.current_order.items:
            self.tree.insert("", "end", values=(
                item.name,
                item.quantity,
                f"{item.price:.2f}€",
                f"{item.total:.2f}€"
            ))
    
    def get_selected_item(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un article!")
            return None
        return self.tree.item(selection[0])["values"][0]  # Nom de l'article
    
    def increment_quantity(self):
        item_name = self.get_selected_item()
        if item_name:
            self.update_callback(item_name, 1)
    
    def decrement_quantity(self):
        item_name = self.get_selected_item()
        if item_name:
            self.update_callback(item_name, -1)
    
    def remove_item(self):
        item_name = self.get_selected_item()
        if item_name:
            if messagebox.askyesno("Confirmation", f"Supprimer {item_name} de la commande?"):
                self.remove_callback(item_name)
