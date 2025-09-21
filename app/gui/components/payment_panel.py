import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from app.services.order_service import OrderService

class PaymentPanel(tk.Frame):
    def __init__(self, parent, order_service: OrderService, 
                 payment_callback: Callable, print_callback: Callable):
        super().__init__(parent, bg="#ffffff", bd=1, relief=tk.RAISED)
        self.order_service = order_service
        self.payment_callback = payment_callback
        self.print_callback = print_callback
        
        self.payment_method = tk.StringVar(value="Espèces")
        
        self.create_widgets()
        self.update_totals()
    
    def create_widgets(self):
        # Titre
        title_label = tk.Label(self, text="💳 PAIEMENT", 
                              font=("Arial", 14, "bold"), bg="#ffffff")
        title_label.pack(pady=10)
        
        # Frame pour les totaux
        total_frame = tk.Frame(self, bg="#ffffff")
        total_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Labels pour les totaux
        self.total_ht_label = tk.Label(total_frame, text="Total HT: 0.00€", 
                                      font=("Arial", 12), bg="#ffffff")
        self.total_ht_label.pack(anchor="w")
        
        self.tva_label = tk.Label(total_frame, text="TVA: 0.00€", 
                                 font=("Arial", 12), bg="#ffffff")
        self.tva_label.pack(anchor="w")
        
        self.total_ttc_label = tk.Label(total_frame, text="Total TTC: 0.00€", 
                                       font=("Arial", 14, "bold"), bg="#ffffff", fg="#2c3e50")
        self.total_ttc_label.pack(anchor="w", pady=(5, 0))
        
        # Séparateur
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=10)
        
        # Méthode de paiement
        payment_frame = tk.Frame(self, bg="#ffffff")
        payment_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(payment_frame, text="Méthode:", font=("Arial", 11), 
                bg="#ffffff").pack(anchor="w")
        
        payment_combo = ttk.Combobox(payment_frame, textvariable=self.payment_method,
                                    values=["Espèces", "Carte Bancaire", "Chèque", "Tickets Restaurant"],
                                    state="readonly", width=20)
        payment_combo.pack(pady=5, anchor="w")
        
        # Boutons d'action
        button_frame = tk.Frame(self, bg="#ffffff")
        button_frame.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Button(button_frame, text="💳 Payer", font=("Arial", 12, "bold"),
                 command=self.process_payment, bg="#27ae60", fg="white",
                 height=2).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        tk.Button(button_frame, text="🖨️ Ticket", font=("Arial", 12),
                 command=self.print_callback, bg="#3498db", fg="white",
                 height=2).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
    
    def update_totals(self):
        order = self.order_service.current_order
        tva_summary = order.tva_summary
        
        total_ht = sum(summary["ht"] for summary in tva_summary.values())
        total_tva = sum(summary["tva"] for summary in tva_summary.values())
        total_ttc = order.total
        
        self.total_ht_label.config(text=f"Total HT: {total_ht:.2f}€")
        self.tva_label.config(text=f"TVA: {total_tva:.2f}€")
        self.total_ttc_label.config(text=f"Total TTC: {total_ttc:.2f}€")

    def process_payment(self):
        """Gère le processus de paiement"""
        try:
            # Vérifier qu'une méthode de paiement est sélectionnée
            payment_method = self.payment_method.get()
            if not payment_method:
                messagebox.showwarning("Attention", "Veuillez sélectionner un moyen de paiement!")
                return

            # Appeler le callback de paiement
            self.payment_callback(payment_method)

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du paiement: {str(e)}")

    def print_ticket(self):
        """Gère l'impression du ticket"""
        try:
            self.print_callback()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'impression: {str(e)}")