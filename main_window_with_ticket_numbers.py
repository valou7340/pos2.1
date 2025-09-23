import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import socket
import os
import json

from ..services.order_service import OrderService

from ..utils.config_loader import ConfigLoader
from .components.menu_panel import MenuPanel
from .components.order_panel import OrderPanel
from .components.payment_panel import PaymentPanel
from .components.report_panel import ReportPanel



class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Caisse Restaurant - La Medusa")
        self.root.geometry("1400x900")
        self.root.configure(bg="#f0f0f0")

        # Services
        self.order_service = OrderService()
        self.menu_data = ConfigLoader.load_menu()
        self.printer_config = ConfigLoader.load_printer_config()

        # Variables
        self.current_table = tk.StringVar(value="Table 1")
        
        # Fichier pour stocker le numéro de ticket
        self.ticket_counter_file = "data/ticket_counter.json"
        self._ensure_data_directory()

        self.create_widgets()
        self.center_window()

    def _ensure_data_directory(self):
        """S'assure que le répertoire data existe"""
        os.makedirs("data", exist_ok=True)

    def _get_next_ticket_number(self):
        """Récupère et incrémente le numéro de ticket"""
        try:
            if os.path.exists(self.ticket_counter_file):
                with open(self.ticket_counter_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    ticket_number = data.get('last_ticket_number', 0) + 1
            else:
                ticket_number = 1
            
            # Sauvegarder le nouveau numéro
            with open(self.ticket_counter_file, 'w', encoding='utf-8') as f:
                json.dump({'last_ticket_number': ticket_number}, f)
            
            return ticket_number
        except Exception as e:
            print(f"Erreur lors de la lecture du numéro de ticket: {e}")
            # En cas d'erreur, utiliser un numéro basé sur l'horodatage
            return int(datetime.datetime.now().strftime("%H%M%S"))

    def _reset_ticket_counter(self):
        """Remet le compteur de tickets à zéro (utile pour les nouveaux jours)"""
        try:
            with open(self.ticket_counter_file, 'w', encoding='utf-8') as f:
                json.dump({'last_ticket_number': 0}, f)
        except Exception as e:
            print(f"Erreur lors de la remise à zéro du compteur: {e}")

    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame, text="🍽️ CAISSE RESTAURANT - LA MEDUSA",
                               font=("Arial", 18, "bold"), fg="white", bg="#2c3e50")
        title_label.pack(side=tk.LEFT, padx=20, pady=15)

        table_frame = tk.Frame(header_frame, bg="#2c3e50")
        table_frame.pack(side=tk.RIGHT, padx=20, pady=15)

        tk.Label(table_frame, text="Table:", font=("Arial", 12),
                 fg="white", bg="#2c3e50").pack(side=tk.LEFT, padx=5)

        table_combo = ttk.Combobox(table_frame, textvariable=self.current_table,
                                   values=self.order_service.get_tables(),
                                   width=12, state="readonly")
        table_combo.pack(side=tk.LEFT)
        table_combo.bind("<<ComboboxSelected>>", self.on_table_change)

        # Bouton Rapports
        report_btn = tk.Button(header_frame, text="📊 Rapports", font=("Arial", 12),
                               command=self.show_reports, bg="#e67e22", fg="white")
        report_btn.pack(side=tk.RIGHT, padx=10, pady=15)

        # Bouton Reset Compteur (pour les administrateurs)
        reset_btn = tk.Button(header_frame, text="🔄 Reset N°", font=("Arial", 10),
                              command=self._confirm_reset_counter, bg="#c0392b", fg="white")
        reset_btn.pack(side=tk.RIGHT, padx=5, pady=15)

        # Content area
        content_frame = tk.Frame(self.root, bg="#f0f0f0")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left side - Menu
        self.menu_panel = MenuPanel(content_frame, self.menu_data, self.add_to_order)
        self.menu_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Right side - Order and Payment
        right_frame = tk.Frame(content_frame, bg="#f0f0f0")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.order_panel = OrderPanel(right_frame, self.order_service,
                                      self.update_quantity, self.remove_from_order)
        self.order_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.payment_panel = PaymentPanel(right_frame, self.order_service,
                                          self.process_payment, self.print_ticket)
        self.payment_panel.pack(fill=tk.BOTH, expand=True)

    def _confirm_reset_counter(self):
        """Demande confirmation avant de remettre le compteur à zéro"""
        result = messagebox.askyesno(
            "Confirmation", 
            "Êtes-vous sûr de vouloir remettre le compteur de tickets à zéro ?\n"
            "Cette action est généralement effectuée en début de journée.",
            icon="warning"
        )
        if result:
            self._reset_ticket_counter()
            messagebox.showinfo("Compteur", "Le compteur de tickets a été remis à zéro.")

    def add_to_order(self, item_name: str, price: float, tva_rate: float, category: str):
        self.order_service.add_to_order(item_name, price, tva_rate, category)
        self.order_panel.update_display()
        self.payment_panel.update_totals()

    def update_quantity(self, item_name: str, delta: int):
        self.order_service.update_quantity(item_name, delta)
        self.order_panel.update_display()
        self.payment_panel.update_totals()

    def remove_from_order(self, item_name: str):
        self.order_service.remove_from_order(item_name)
        self.order_panel.update_display()
        self.payment_panel.update_totals()

    def process_payment(self, payment_method: str):
        if not self.order_service.current_order.items:
            messagebox.showwarning("Attention", "Aucun article dans la commande!")
            return

        try:
            self.order_service.process_payment(payment_method)
            self.order_panel.update_display()
            self.payment_panel.update_totals()
            messagebox.showinfo("Paiement", f"Paiement {payment_method} accepté!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du paiement: {str(e)}")

    def print_ticket(self):
        """Imprime le ticket de caisse et les tickets de préparation"""
        if not self.order_service.current_order.items:
            messagebox.showwarning("Attention", "Aucun article dans la commande!")
            return

        try:
            order = self.order_service.current_order
            table = order.table
            
            # Obtenir le numéro de ticket
            ticket_number = self._get_next_ticket_number()

            # Imprimer le ticket de caisse (client)
            self._print_receipt_ticket(order, ticket_number)

            # Imprimer les tickets de préparation si nécessaire
            self._print_kitchen_tickets(order, ticket_number)

            messagebox.showinfo("Impression", f"Ticket n°{ticket_number} imprimé avec succès!")

        except Exception as e:
            messagebox.showerror("Erreur d'impression", f"Erreur lors de l'impression: {str(e)}")

    def _print_receipt_ticket(self, order, ticket_number):
        """Imprime le ticket de caisse pour le client"""
        if not self.printer_config["receipt_printer"]["enabled"]:
            return

        try:
            printer_config = self.printer_config["receipt_printer"]
            ip = printer_config["ip"]
            port = printer_config["port"]
            timeout = printer_config["timeout"]

            # Connexion à l'imprimante
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))

            # Préparation du contenu du ticket
            content = self._generate_receipt_content(order, ticket_number)

            # Envoi des données à l'imprimante
            sock.sendall(content.encode('utf-8'))
            sock.close()

        except Exception as e:
            print(f"Erreur impression ticket caisse: {e}")
            raise

    def _print_kitchen_tickets(self, order, ticket_number):
        """Imprime les tickets de préparation pour la cuisine/bar"""
        # Vérifier s'il y a des articles alimentaires pour la cuisine
        food_items = [item for item in order.items if item.category == "alimentation"]
        if food_items and self.printer_config["kitchen_printer"]["enabled"]:
            self._print_preparation_ticket(order, food_items, "CUISINE", 
                                         self.printer_config["kitchen_printer"], ticket_number)

        # Vérifier s'il y a des boissons pour le bar
        drink_items = [item for item in order.items if item.category in ["alcool", "boisson sans alcool"]]
        if drink_items and self.printer_config["bar_printer"]["enabled"]:
            self._print_preparation_ticket(order, drink_items, "BAR", 
                                         self.printer_config["bar_printer"], ticket_number)

    def _print_preparation_ticket(self, order, items, destination, printer_config, ticket_number):
        """Imprime un ticket de préparation"""
        try:
            ip = printer_config["ip"]
            port = printer_config["port"]
            timeout = printer_config["timeout"]

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))

            # Préparation du contenu du ticket de préparation
            content = self._generate_preparation_content(order, items, destination, ticket_number)

            # Envoi des données à l'imprimante
            sock.sendall(content.encode('utf-8'))
            sock.close()

        except Exception as e:
            print(f"Erreur impression ticket {destination}: {e}")

    def _generate_receipt_content(self, order, ticket_number):
        """Génère le contenu du ticket de caisse"""
        content = []

        # En-tête du ticket
        content.append("\x1B\x40")  # Initialize printer
        content.append("\x1B\x61\x01")  # Center align
        content.append("\x1B\x21\x30")  # Double height and width
        content.append("LA MEDUSA\n")
        content.append("\x1B\x21\x00")  # Normal text
        content.append("1 Avenue Pasteur\n")
        content.append("06670 ST Martin Du Var\n")
        content.append("Siret: 983 591 389 00017\n")
        content.append("-----------------------------\n")
        content.append(f"TICKET N°: {ticket_number:06d}\n")  # Numéro de ticket formaté sur 6 chiffres
        content.append(f"Table: {order.table}\n")
        content.append(f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        content.append("-----------------------------\n")
        content.append("\x1B\x61\x00")  # Left align

        # Articles
        content.append("\x1B\x21\x10")  # Emphasized
        content.append("ARTICLE          QTE   PRIX\n")
        content.append("\x1B\x21\x00")  # Normal text
        content.append("-----------------------------\n")

        for item in order.items:
            name = item.name[:16]  # Limiter la longueur du nom
            qty = str(item.quantity)
            price = f"{item.total:.2f}EUR"
            content.append(f"{name:<16} {qty:>3} {price:>6}\n")

        # Total
        content.append("-----------------------------\n")
        content.append("\x1B\x61\x00")
        content.append(f"TOTAL: {order.total:.2f}EUR\n")

        # Détail TVA
        content.append("\x1B\x61\x00")  # Left align
        content.append("-----------------------------\n")
        tva_summary = order.tva_summary
        for rate, details in tva_summary.items():
            content.append(f"TVA {rate}%: {details['tva']:.2f}EUR\n")

        # Pied de page
        content.append("-----------------------------\n")
        content.append("\x1B\x61\x01")  # Center align
        content.append("Merci pour votre visite !\n")
        content.append(f"Ticket: {ticket_number:06d}\n")  # Répéter le numéro en pied de page
        content.append("\n\n\n")

        # Couper le papier
        content.append("\x1D\x56\x00")  # Cut paper

        return "".join(content)

    def _generate_preparation_content(self, order, items, destination, ticket_number):
        """Génère le contenu du ticket de préparation"""
        content = []

        # En-tête du ticket
        content.append("\x1B\x40")  # Initialize printer
        content.append("\x1B\x61\x01")  # Center align
        content.append("\x1B\x21\x30")  # Double height and width
        content.append(f"{destination}\n")
        content.append("\x1B\x21\x00")  # Normal text
        content.append("-----------------------------\n")
        content.append(f"TICKET N°: {ticket_number:06d}\n")  # Numéro de ticket
        content.append(f"Table: {order.table}\n")
        content.append(f"Heure: {datetime.datetime.now().strftime('%H:%M')}\n")
        content.append(f"Commande: {len(items)} article(s)\n")
        content.append("-----------------------------\n")
        content.append("\x1B\x61\x00")  # Left align

        # Articles
        content.append("\x1B\x21\x10")  # Emphasized
        content.append("ARTICLE          QTE\n")
        content.append("\x1B\x21\x00")  # Normal text
        content.append("-----------------------------\n")

        for item in items:
            name = item.name[:16]  # Limiter la longueur du nom
            qty = str(item.quantity)
            content.append(f"{name:<16} {qty:>3}\n")

        # Notes spéciales
        content.append("-----------------------------\n")
        content.append("NOTES:\n")
        content.append("-----------------------------\n")
        content.append(f"Ticket: {ticket_number:06d}\n")  # Numéro de ticket en bas
        content.append("\n\n")

        # Couper le papier
        content.append("\x1D\x56\x00")  # Cut paper

        return "".join(content)

    def on_table_change(self, event=None):
        self.order_service.switch_table(self.current_table.get())
        self.order_panel.update_display()
        self.payment_panel.update_totals()

    def center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")

    def show_reports(self):
        """Affiche la fenêtre des rapports"""
        report_window = ReportPanel(self.root, self.order_service)
        report_window.grab_set()