import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from app.models.order import Order, OrderItem

class OrderService:
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.current_table = "Table 1"
        self.daily_sales = self._load_daily_sales()
    
    @property
    def current_order(self) -> Order:
        if self.current_table not in self.orders:
            self.orders[self.current_table] = Order(table=self.current_table)
        return self.orders[self.current_table]
    
    def switch_table(self, table: str) -> None:
        self.current_table = table
    
    def add_to_order(self, name: str, price: float, tva_rate: float, category: str) -> None:
        item = OrderItem(name=name, price=price, tva_rate=tva_rate, category=category)
        self.current_order.add_item(item)
    
    def remove_from_order(self, item_name: str) -> None:
        self.current_order.remove_item(item_name)
    
    def update_quantity(self, item_name: str, delta: int) -> None:
        self.current_order.update_quantity(item_name, delta)
    
    def clear_current_order(self) -> None:
        self.orders[self.current_table] = Order(table=self.current_table)
    
    def process_payment(self, payment_method: str) -> None:
        self.current_order.payment_method = payment_method
        self.current_order.is_paid = True
        self.save_sale(self.current_order)
        self.clear_current_order()
    
    def save_sale(self, order: Order) -> None:
        # Créer le dossier du mois si nécessaire
        now = datetime.now()
        month_fr = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ][now.month - 1]
        
        folder_name = f"Vente {month_fr} {now.year}"
        os.makedirs(folder_name, exist_ok=True)
        
        # Charger les ventes existantes ou créer une nouvelle liste
        sales_file = os.path.join(folder_name, "vente.json")
        sales = []
        
        if os.path.exists(sales_file):
            try:
                with open(sales_file, 'r', encoding='utf-8') as f:
                    sales = json.load(f)
            except:
                sales = []
        
        # Ajouter la nouvelle vente
        sales.append(order.to_dict())
        
        # Sauvegarder
        with open(sales_file, 'w', encoding='utf-8') as f:
            json.dump(sales, f, ensure_ascii=False, indent=2)
    
    def get_tables(self) -> List[str]:
        return [f"Table {i}" for i in range(1, 21)] + ["À emporter", "Comptoir"]

    def _load_daily_sales(self) -> Dict[str, any]:
        """Charge les ventes du jour"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        sales_file = f"ventes_jour_{today_str}.json"

        if os.path.exists(sales_file):
            try:
                with open(sales_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        # Structure initiale pour les ventes du jour
        return {
            "date": today_str,
            "total_ventes_ht": 0.0,
            "total_ventes_ttc": 0.0,
            "total_tva": 0.0,
            "ventes_par_taux": {},
            "nombre_transactions": 0,
            "ventes_par_moyen_paiement": {},
            "transactions": []
        }

    def _save_daily_sales(self):
        """Sauvegarde les ventes du jour"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        sales_file = f"ventes_jour_{today_str}.json"

        with open(sales_file, 'w', encoding='utf-8') as f:
            json.dump(self.daily_sales, f, ensure_ascii=False, indent=2)

    def process_payment(self, payment_method: str) -> None:
        self.current_order.payment_method = payment_method
        self.current_order.is_paid = True

        # Mettre à jour les statistiques du jour
        self._update_daily_sales(self.current_order)

        self.save_sale(self.current_order)
        self.clear_current_order()
        self._save_daily_sales()  # Sauvegarder après chaque vente

    def _update_daily_sales(self, order: Order):
        """Met à jour les statistiques des ventes du jour"""
        # Compter la transaction
        self.daily_sales["nombre_transactions"] += 1

        # Ajouter aux totaux
        tva_summary = order.tva_summary
        total_ht = sum(summary["ht"] for summary in tva_summary.values())

        self.daily_sales["total_ventes_ht"] += total_ht
        self.daily_sales["total_ventes_ttc"] += order.total
        self.daily_sales["total_tva"] += (order.total - total_ht)

        # Ventes par taux de TVA
        for taux, details in tva_summary.items():
            if str(taux) not in self.daily_sales["ventes_par_taux"]:
                self.daily_sales["ventes_par_taux"][str(taux)] = {
                    "ht": 0.0,
                    "tva": 0.0,
                    "ttc": 0.0
                }
            self.daily_sales["ventes_par_taux"][str(taux)]["ht"] += details["ht"]
            self.daily_sales["ventes_par_taux"][str(taux)]["tva"] += details["tva"]
            self.daily_sales["ventes_par_taux"][str(taux)]["ttc"] += details["ttc"]

        # Ventes par moyen de paiement
        if order.payment_method not in self.daily_sales["ventes_par_moyen_paiement"]:
            self.daily_sales["ventes_par_moyen_paiement"][order.payment_method] = 0.0
        self.daily_sales["ventes_par_moyen_paiement"][order.payment_method] += order.total

        # Ajouter la transaction à l'historique
        self.daily_sales["transactions"].append({
            "heure": datetime.now().strftime("%H:%M:%S"),
            "table": order.table,
            "montant": order.total,
            "moyen_paiement": order.payment_method
        })

    def generate_z_report(self) -> Dict[str, any]:
        """Génère le rapport Z du jour"""
        today = datetime.now()
        report = {
            "type": "RAPPORT_Z",
            "date_emission": today.strftime("%Y-%m-%d %H:%M:%S"),
            "date_comptable": today.strftime("%Y-%m-%d"),
            "numero_rapport": self._get_next_report_number(),
            **self.daily_sales  # Inclut toutes les données du jour
        }

        # Sauvegarder le rapport Z
        self._save_z_report(report)

        # Réinitialiser les ventes du jour pour le prochain rapport
        self._reset_daily_sales()

        return report

    def _get_next_report_number(self) -> int:
        """Retourne le prochain numéro de rapport"""
        try:
            with open("dernier_rapport.txt", "r") as f:
                last_number = int(f.read().strip())
        except:
            last_number = 0

        next_number = last_number + 1

        with open("dernier_rapport.txt", "w") as f:
            f.write(str(next_number))

        return next_number

    def _save_z_report(self, report: Dict[str, any]):
        """Sauvegarde le rapport Z"""
        reports_dir = "rapports_z"
        os.makedirs(reports_dir, exist_ok=True)

        filename = f"rapport_z_{report['numero_rapport']:04d}_{report['date_comptable']}.json"
        filepath = os.path.join(reports_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    def _reset_daily_sales(self):
        """Réinitialise les ventes du jour après un rapport Z"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.daily_sales = {
            "date": today_str,
            "total_ventes_ht": 0.0,
            "total_ventes_ttc": 0.0,
            "total_tva": 0.0,
            "ventes_par_taux": {},
            "nombre_transactions": 0,
            "ventes_par_moyen_paiement": {},
            "transactions": []
        }
        self._save_daily_sales()

    def get_current_day_summary(self) -> Dict[str, any]:
        """Retourne le résumé des ventes du jour en cours"""
        return self.daily_sales.copy()

    def print_z_report(self, report: Dict[str, any]):
        """Imprime le rapport Z"""
        if not self.printer_config["receipt_printer"]["enabled"]:
            return

        try:
            import socket

            printer_config = self.printer_config["receipt_printer"]
            ip = printer_config["ip"]
            port = printer_config["port"]

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, port))

            content = self._generate_z_report_content(report)
            sock.sendall(content.encode('utf-8'))
            sock.close()

        except Exception as e:
            print(f"Erreur impression rapport Z: {e}")

    def _generate_z_report_content(self, report: Dict[str, any]) -> str:
        """Génère le contenu ESC/POS pour le rapport Z"""
        content = []

        content.append("\x1B\x40")  # Initialize printer
        content.append("\x1B\x61\x01")  # Center align
        content.append("\x1B\x21\x30")  # Double height and width
        content.append("RAPPORT Z\n")
        content.append("\x1B\x21\x00")  # Normal text
        content.append("LA MEDUSA\n")
        content.append("-----------------------------\n")
        content.append(f"N°: {report['numero_rapport']:04d}\n")
        content.append(f"Date: {report['date_emission']}\n")
        content.append("-----------------------------\n")

        # Totaux
        content.append("\x1B\x21\x10")  # Emphasized
        content.append("TOTAL GENERAL\n")
        content.append("\x1B\x21\x00")  # Normal text
        content.append(f"HT:   {report['total_ventes_ht']:10.2f}€\n")
        content.append(f"TVA:  {report['total_tva']:10.2f}€\n")
        content.append(f"TTC:  {report['total_ventes_ttc']:10.2f}€\n")
        content.append(f"Transactions: {report['nombre_transactions']:4d}\n")
        content.append("-----------------------------\n")

        # Détail TVA
        content.append("DETAIL TVA\n")
        for taux, details in report['ventes_par_taux'].items():
            content.append(f"TVA {taux}%: {details['ttc']:8.2f}€\n")

        content.append("-----------------------------\n")

        # Moyens de paiement
        content.append("MOYENS DE PAIEMENT\n")
        for moyen, montant in report['ventes_par_moyen_paiement'].items():
            content.append(f"{moyen:<15} {montant:8.2f}€\n")

        content.append("-----------------------------\n")
        content.append("\x1B\x61\x01")  # Center align
        content.append("*** RAPPORT Z ***\n")
        content.append("Fin de rapport\n\n\n")
        content.append("\x1D\x56\x00")  # Cut paper

        return "".join(content)