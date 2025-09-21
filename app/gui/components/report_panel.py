import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from datetime import datetime
from app.services.order_service import OrderService


class ReportPanel(tk.Toplevel):
    def __init__(self, parent, order_service: OrderService):
        super().__init__(parent)
        self.order_service = order_service
        self.title("Rapports - La Medusa")
        self.geometry("800x600")
        self.configure(bg="#f0f0f0")

        self.create_widgets()
        self.update_summary()
        self.center_window()

    def create_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self, bg="#f0f0f0", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Titre
        title_label = tk.Label(main_frame, text="📊 RAPPORTS JOURNALIERS",
                               font=("Arial", 16, "bold"), bg="#f0f0f0")
        title_label.pack(pady=(0, 20))

        # Résumé du jour
        summary_frame = tk.LabelFrame(main_frame, text="Résumé du jour",
                                      font=("Arial", 12, "bold"), bg="#f0f0f0")
        summary_frame.pack(fill=tk.X, pady=(0, 20))

        self.summary_labels = {}
        metrics = [
            ("Total TTC", "total_ventes_ttc", "€"),
            ("Total HT", "total_ventes_ht", "€"),
            ("Total TVA", "total_tva", "€"),
            ("Transactions", "nombre_transactions", "")
        ]

        for i, (label, key, unit) in enumerate(metrics):
            frame = tk.Frame(summary_frame, bg="#f0f0f0")
            frame.grid(row=i // 2, column=i % 2, padx=10, pady=5, sticky="w")

            tk.Label(frame, text=f"{label}:", font=("Arial", 10),
                     bg="#f0f0f0").pack(anchor="w")
            self.summary_labels[key] = tk.Label(frame, text="0",
                                                font=("Arial", 10, "bold"),
                                                bg="#f0f0f0", fg="#2c3e50")
            self.summary_labels[key].pack(anchor="w")

        # TVA par taux
        tva_frame = tk.LabelFrame(main_frame, text="Détail TVA",
                                  font=("Arial", 12, "bold"), bg="#f0f0f0")
        tva_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        columns = ("taux", "ht", "tva", "ttc")
        self.tva_tree = ttk.Treeview(tva_frame, columns=columns, show="headings", height=4)

        for col, text in zip(columns, ["Taux TVA", "Total HT", "TVA", "Total TTC"]):
            self.tva_tree.heading(col, text=text)
            self.tva_tree.column(col, width=100, anchor="e")

        self.tva_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Moyens de paiement
        payment_frame = tk.LabelFrame(main_frame, text="Moyens de paiement",
                                      font=("Arial", 12, "bold"), bg="#f0f0f0")
        payment_frame.pack(fill=tk.X, pady=(0, 20))

        columns = ("moyen", "montant")
        self.payment_tree = ttk.Treeview(payment_frame, columns=columns, show="headings", height=3)

        for col, text in zip(columns, ["Moyen", "Montant"]):
            self.payment_tree.heading(col, text=text)
            self.payment_tree.column(col, width=150, anchor="e")

        self.payment_tree.pack(fill=tk.X, padx=5, pady=5)

        # Boutons d'action
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(button_frame, text="🔄 Actualiser", font=("Arial", 10),
                  command=self.update_summary, bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="📄 Rapport Z", font=("Arial", 10, "bold"),
                  command=self.generate_z_report, bg="#27ae60", fg="white").pack(side=tk.RIGHT, padx=5)

        tk.Button(button_frame, text="💾 Exporter", font=("Arial", 10),
                  command=self.export_report, bg="#f39c12", fg="white").pack(side=tk.RIGHT, padx=5)

    def update_summary(self):
        """Met à jour l'affichage du résumé"""
        summary = self.order_service.get_current_day_summary()

        # Métriques principales
        self.summary_labels["total_ventes_ttc"].config(text=f"{summary['total_ventes_ttc']:.2f}€")
        self.summary_labels["total_ventes_ht"].config(text=f"{summary['total_ventes_ht']:.2f}€")
        self.summary_labels["total_tva"].config(text=f"{summary['total_tva']:.2f}€")
        self.summary_labels["nombre_transactions"].config(text=f"{summary['nombre_transactions']}")

        # Détail TVA
        for item in self.tva_tree.get_children():
            self.tva_tree.delete(item)

        for taux, details in summary["ventes_par_taux"].items():
            self.tva_tree.insert("", "end", values=(
                f"{taux}%",
                f"{details['ht']:.2f}€",
                f"{details['tva']:.2f}€",
                f"{details['ttc']:.2f}€"
            ))

        # Moyens de paiement
        for item in self.payment_tree.get_children():
            self.payment_tree.delete(item)

        for moyen, montant in summary["ventes_par_moyen_paiement"].items():
            self.payment_tree.insert("", "end", values=(
                moyen,
                f"{montant:.2f}€"
            ))

    def generate_z_report(self):
        """Génère le rapport Z"""
        if messagebox.askyesno("Confirmation",
                               "Êtes-vous sûr de vouloir générer le rapport Z ?\n\n"
                               "Cette action réinitialisera les compteurs du jour."):
            try:
                report = self.order_service.generate_z_report()
                messagebox.showinfo("Succès",
                                    f"Rapport Z #{report['numero_rapport']} généré avec succès!\n\n"
                                    f"Total TTC: {report['total_ventes_ttc']:.2f}€\n"
                                    f"Nombre de transactions: {report['nombre_transactions']}")
                self.update_summary()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération du rapport: {str(e)}")

    def export_report(self):
        """Exporte le rapport en CSV"""
        # Implémentation de l'export CSV
        messagebox.showinfo("Info", "Fonction d'export à implémenter")

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")