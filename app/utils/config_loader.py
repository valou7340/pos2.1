import json
import os
from typing import Dict, Any, List
from pathlib import Path

class ConfigLoader:
    @staticmethod
    def load_config(file_path: str, default_config: Dict[str, Any] = None) -> Dict[str, Any]:
        if default_config is None:
            default_config = {}
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement de {file_path}: {e}")
        
        return default_config
    
    @staticmethod
    def load_menu() -> Dict[str, Any]:
        """Charge le menu depuis le fichier JSON"""
        # Déterminer le chemin absolu du fichier menu
        base_dir = Path(__file__).resolve().parent.parent.parent
        menu_path = base_dir / 'config' / 'menu_restaurant.json'
        
        default_menu = {
            "Entrées": {
                "tva_rate": 10,
                "category": "alimentation",
                "items": {"Salade César": 8.5, "Charcuterie": 18.0}
            }
        }
        
        return ConfigLoader.load_config(str(menu_path), default_menu)
    
    @staticmethod
    def load_printer_config() -> Dict[str, Any]:
        """Charge la configuration des imprimantes"""
        base_dir = Path(__file__).resolve().parent.parent.parent
        printer_path = base_dir / 'config' / 'printer_config.json'
        
        default_config = {
            "kitchen_printer": {
                "enabled": True,
                "ip": "192.168.1.100",
                "port": 9100,
                "timeout": 5,
                "name": "Imprimante Cuisine"
            },
            "receipt_printer": {
                "enabled": True,
                "ip": "192.168.1.101",
                "port": 9100,
                "timeout": 5,
                "name": "Imprimante Tickets"
            },
            "bar_printer": {
                "enabled": False,
                "ip": "192.168.1.102",
                "port": 9100,
                "timeout": 5,
                "name": "Imprimante Bar"
            }
        }
        
        return ConfigLoader.load_config(str(printer_path), default_config)
    
    @staticmethod
    def get_menu_categories() -> List[str]:
        """Retourne la liste des catégories du menu"""
        menu_data = ConfigLoader.load_menu()
        return list(menu_data.keys())
    
    @staticmethod
    def get_menu_items_by_category(category: str) -> Dict[str, float]:
        """Retourne les items d'une catégorie spécifique"""
        menu_data = ConfigLoader.load_menu()
        if category in menu_data:
            return menu_data[category].get("items", {})
        return {}
    
    @staticmethod
    def get_item_details(category: str, item_name: str) -> Dict[str, Any]:
        """Retourne les détails d'un item spécifique"""
        menu_data = ConfigLoader.load_menu()
        if category in menu_data:
            category_data = menu_data[category]
            if item_name in category_data.get("items", {}):
                return {
                    "price": category_data["items"][item_name],
                    "tva_rate": category_data.get("tva_rate", 10.0),
                    "category": category_data.get("category", "alimentation")
                }
        return None
    
    @staticmethod
    def save_menu(new_menu_data: Dict[str, Any]) -> bool:
        """Sauvegarde le menu dans le fichier JSON"""
        try:
            base_dir = Path(__file__).resolve().parent.parent.parent
            menu_path = base_dir / 'config' / 'menu_restaurant.json'
            
            with open(menu_path, 'w', encoding='utf-8') as f:
                json.dump(new_menu_data, f, ensure_ascii=False, indent=2)
            
            print("Menu sauvegardé avec succès!")
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du menu: {e}")
            return False
