import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import socket

from ..services.order_service import OrderService
from ..utils import config_loader
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

        self.create_widgets()
        self.center_window()

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

            # Imprimer le ticket de caisse (client)
            self._print_receipt_ticket(order)

            # Imprimer les tickets de préparation si nécessaire
            self._print_kitchen_tickets(order)

            messagebox.showinfo("Impression", "Ticket(s) imprimé(s) avec succès!")

        except Exception as e:
            messagebox.showerror("Erreur d'impression", f"Erreur lors de l'impression: {str(e)}")

    def _print_receipt_ticket(self, order):
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
            content = self._generate_receipt_content(order)

            # Envoi des données à l'imprimante
            sock.sendall(content.encode('utf-8'))
            sock.close()

        except Exception as e:
            print(f"Erreur impression ticket caisse: {e}")
            raise

    def _print_kitchen_tickets(self, order):
        """Imprime les tickets de préparation pour la cuisine/bar"""
        # Vérifier s'il y a des articles alimentaires pour la cuisine
        food_items = [item for item in order.items if item.category == "alimentation"]
        if food_items and self.printer_config["kitchen_printer"]["enabled"]:
            self._print_preparation_ticket(order, food_items, "CUISINE", self.printer_config["kitchen_printer"])

        # Vérifier s'il y a des boissons pour le bar
        drink_items = [item for item in order.items if item.category in ["alcool", "boisson sans alcool"]]
        if drink_items and self.printer_config["bar_printer"]["enabled"]:
            self._print_preparation_ticket(order, drink_items, "BAR", self.printer_config["bar_printer"])

    def _print_preparation_ticket(self, order, items, destination, printer_config):
        """Imprime un ticket de préparation"""
        try:
            ip = printer_config["ip"]
            port = printer_config["port"]
            timeout = printer_config["timeout"]

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))

            # Préparation du contenu du ticket de préparation
            content = self._generate_preparation_content(order, items, destination)

            # Envoi des données à l'imprimante
            sock.sendall(content.encode('utf-8'))
            sock.close()

        except Exception as e:
            print(f"Erreur impression ticket {destination}: {e}")

    def _generate_receipt_content(self, order):
        """Génère le contenu du ticket de caisse"""
        content = []

        # En-tête du ticket
        content.append("\x1B\x40")  # Initialize printer
        content.append("\x1B\x61\x01")  # Center align
        content.append("\x1B\x21\x30")  # Double height and width
        content.append("LA MEDUSA\n")
        content.append("\x1B\x21\x00")  # Normal text
        content.append("RESTAURANT\n")
        content.append("-----------------------------\n")
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
            price = f"{item.total:.2f}€"
            content.append(f"{name:<16} {qty:>3} {price:>6}\n")

        # Total
        content.append("-----------------------------\n")
        content.append("\x1B\x61\x02")  # Right align
        content.append(f"TOTAL: {order.total:.2f}€\n")

        # Détail TVA
        content.append("\x1B\x61\x00")  # Left align
        content.append("-----------------------------\n")
        tva_summary = order.tva_summary
        for rate, details in tva_summary.items():
            content.append(f"TVA {rate}%: {details['tva']:.2f}€\n")

        # Pied de page
        content.append("-----------------------------\n")
        content.append("\x1B\x61\x01")  # Center align
        content.append("Merci pour votre visite !\n")
        content.append("A bientôt !\n\n\n")

        # Couper le papier
        content.append("\x1D\x56\x00")  # Cut paper

        return "".join(content)

    def _generate_preparation_content(self, order, items, destination):
        """Génère le contenu du ticket de préparation"""
        content = []

        # En-tête du ticket
        content.append("\x1B\x40")  # Initialize printer
        content.append("\x1B\x61\x01")  # Center align
        content.append("\x1B\x21\x30")  # Double height and width
        content.append(f"{destination}\n")
        content.append("\x1B\x21\x00")  # Normal text
        content.append("-----------------------------\n")
        content.append(f"Table: {order.table}\n")
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
        content.append("-----------------------------\n\n\n")

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
