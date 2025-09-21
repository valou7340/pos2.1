from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime

@dataclass
class OrderItem:
    name: str
    price: float
    quantity: int = 1
    tva_rate: float = 10.0
    category: str = "alimentation"
    
    @property
    def total(self) -> float:
        return self.price * self.quantity
    
    @property
    def tva_amount(self) -> float:
        return self.total - (self.total / (1 + self.tva_rate / 100))

@dataclass
class Order:
    table: str = "Table 1"
    items: List[OrderItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    payment_method: str = ""
    is_paid: bool = False
    
    def add_item(self, item: OrderItem) -> None:
        for existing_item in self.items:
            if existing_item.name == item.name:
                existing_item.quantity += item.quantity
                return
        self.items.append(item)
    
    def remove_item(self, item_name: str) -> None:
        self.items = [item for item in self.items if item.name != item_name]
    
    def update_quantity(self, item_name: str, delta: int) -> None:
        for item in self.items:
            if item.name == item_name:
                item.quantity += delta
                if item.quantity <= 0:
                    self.remove_item(item_name)
                break
    
    @property
    def total(self) -> float:
        return sum(item.total for item in self.items)
    
    @property
    def tva_summary(self) -> Dict[float, Dict[str, float]]:
        summary = {}
        for item in self.items:
            if item.tva_rate not in summary:
                summary[item.tva_rate] = {"ht": 0, "tva": 0, "ttc": 0}
            
            ht = item.total / (1 + item.tva_rate / 100)
            tva = item.total - ht
            
            summary[item.tva_rate]["ht"] += ht
            summary[item.tva_rate]["tva"] += tva
            summary[item.tva_rate]["ttc"] += item.total
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "table": self.table,
            "items": [
                {
                    "name": item.name,
                    "price": item.price,
                    "quantity": item.quantity,
                    "tva_rate": item.tva_rate,
                    "category": item.category
                }
                for item in self.items
            ],
            "total": self.total,
            "payment_method": self.payment_method,
            "is_paid": self.is_paid,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        order = cls(
            table=data.get("table", "Table 1"),
            payment_method=data.get("payment_method", ""),
            is_paid=data.get("is_paid", False)
        )
        
        if "created_at" in data:
            order.created_at = datetime.fromisoformat(data["created_at"])
        
        for item_data in data.get("items", []):
            order.add_item(OrderItem(
                name=item_data["name"],
                price=item_data["price"],
                quantity=item_data["quantity"],
                tva_rate=item_data.get("tva_rate", 10.0),
                category=item_data.get("category", "alimentation")
            ))
        
        return order
