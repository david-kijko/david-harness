A test in our payments service is failing intermittently in CI. Find the root cause.

THE FAILING TEST (in `tests/test_invoice.py`):
```python
def test_invoice_total_with_promo():
    invoice = Invoice(customer_id="C1")
    invoice.add_line(Item(sku="A", price=10.00), qty=2)
    invoice.add_line(Item(sku="B", price=5.00), qty=1)
    invoice.apply_promo(PercentOff(percent=10))
    assert invoice.total() == 22.50  # (10*2 + 5) * 0.9
```

It usually passes. About 1 in 8 CI runs it fails with `AssertionError: 22.5 != 25.0`.

THE PRODUCTION CODE:

`src/invoice.py`:
```python
class Invoice:
    def __init__(self, customer_id):
        self.customer_id = customer_id
        self.lines = []
        self.promos = []

    def add_line(self, item, qty):
        self.lines.append(Line(item=item, qty=qty))

    def apply_promo(self, promo):
        self.promos.append(promo)

    def total(self):
        subtotal = sum(line.item.price * line.qty for line in self.lines)
        for promo in self.promos:
            subtotal = promo.apply(subtotal)
        return round(subtotal, 2)
```

`src/promo.py`:
```python
class PercentOff:
    def __init__(self, percent):
        self.percent = percent
        self._applied = False

    def apply(self, amount):
        if self._applied:
            return amount
        self._applied = True
        return amount * (1 - self.percent / 100)
```

`src/line.py`:
```python
from dataclasses import dataclass

@dataclass
class Line:
    item: object
    qty: int
```

`src/item.py`:
```python
from dataclasses import dataclass

@dataclass
class Item:
    sku: str
    price: float
```

The CI runner uses pytest with `-p no:randomly` and 8 parallel workers (`pytest-xdist`).

QUESTION: Where is the bug, and why does it only fail ~1 in 8 runs? Identify the specific file:line that needs to change and explain the mechanism.
