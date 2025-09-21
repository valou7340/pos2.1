import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

class MenuLoader:
    @staticmethod
    def get_menu_path() -> Path:
        """Retourne le chemin absolu vers le fichier menu"""
        return Path(__file__).resolve().parent.parent.parent / 'config' / 'menu_restaurant.json'
    
    @staticmethod
    def load_menu() -> Dict[str, Any]:
        """Charge le menu depuis le fichier JSON"""
        menu_path = MenuLoader.get_menu_path()
        
        # Menu par défaut si le fichier n'existe pas
        default_menu = {
            "Entrées": {
                "tva_rate": 10,
                "category": "alimentation",
                "items": {"Salade César": 8.5, "Charcuterie": 18.0}
            }
        }
        
        if menu_path.exists():
            try:
                with open(menu_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement du menu: {e}")
                return default_menu
        else:
            print(f"Fichier menu non trouvé: {menu_path}")
            return default_menu
    
    @staticmethod
    def get_all_categories() -> List[str]:
        """Retourne toutes les catégories du menu"""
        menu = MenuLoader.load_menu()
        return list(menu.keys())
    
    @staticmethod
    def get_items_by_category(category: str) -> Dict[str, float]:
        """Retourne tous les items d'une catégorie"""
        menu = MenuLoader.load_menu()
        return menu.get(category, {}).get("items", {})
    
    @staticmethod
    def get_category_info(category: str) -> Dict[str, Any]:
        """Retourne les informations d'une catégorie (tva_rate, category)"""
        menu = MenuLoader.load_menu()
        return menu.get(category, {})
    
    @staticmethod
    def search_item(item_name: str) -> Optional[Dict[str, Any]]:
        """Recherche un item dans tout le menu"""
        menu = MenuLoader.load_menu()
        
        for category, category_data in menu.items():
            if item_name in category_data.get("items", {}):
                return {
                    "name": item_name,
                    "price": category_data["items"][item_name],
                    "tva_rate": category_data.get("tva_rate", 10.0),
                    "category": category_data.get("category", "alimentation"),
                    "menu_category": category
                }
        return None
    
    @staticmethod
    def update_menu(new_menu_data: Dict[str, Any]) -> bool:
        """Met à jour le fichier menu"""
        try:
            menu_path = MenuLoader.get_menu_path()
            
            # S'assurer que le dossier config existe
            menu_path.parent.mkdir(exist_ok=True)
            
            with open(menu_path, 'w', encoding='utf-8') as f:
                json.dump(new_menu_data, f, ensure_ascii=False, indent=2)
            
            print("Menu mis à jour avec succès!")
            return True
        except Exception as e:
            print(f"Erreur lors de la mise à jour du menu: {e}")
            return False

# Fonction utilitaire simple pour un accès rapide
def load_menu() -> Dict[str, Any]:
    """Charge le menu depuis le fichier JSON (fonction simplifiée)"""
    return MenuLoader.load_menu()
