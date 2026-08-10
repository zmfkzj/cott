
from cott_runtime import CottList, Err, Ok, Result
from curriculum.billing_system_types import BillTotals, BillingError, BillingError_DuplicateItem, BillingError_NegativeQuantity, BillingError_WrongCategory, BillingItem_Coke, BillingItem_Daal, BillingItem_Dettol, BillingItem_Fanta, BillingItem_Flour, BillingItem_FoodOil, BillingItem_HandGloves, BillingItem_Limka, BillingItem_Maggi, BillingItem_Mask, BillingItem_MountainDuo, BillingItem_Mazza, BillingItem_Newsprin, BillingItem_Rice, BillingItem_Sanitizer, BillingItem_Sprite, BillingItem_ThermalGun, BillingItem_Wheat, Quantity


def calculate_bill(medical: CottList[Quantity], grocery: CottList[Quantity], drinks: CottList[Quantity]) -> Result[BillTotals, BillingError]:
    medical_items: tuple[type[object], ...] = (
        BillingItem_Sanitizer,
        BillingItem_Mask,
        BillingItem_HandGloves,
        BillingItem_Dettol,
        BillingItem_Newsprin,
        BillingItem_ThermalGun,
    )
    grocery_items: tuple[type[object], ...] = (
        BillingItem_Rice,
        BillingItem_FoodOil,
        BillingItem_Wheat,
        BillingItem_Daal,
        BillingItem_Flour,
        BillingItem_Maggi,
    )
    drinks_items: tuple[type[object], ...] = (
        BillingItem_Sprite,
        BillingItem_Limka,
        BillingItem_Mazza,
        BillingItem_Coke,
        BillingItem_Fanta,
        BillingItem_MountainDuo,
    )
    bill_categories: tuple[CottList[Quantity], CottList[Quantity], CottList[Quantity]] = (medical, grocery, drinks)

    for lines in bill_categories:
        for line in lines:
            if line.quantity < 0:
                return Err(error=BillingError_NegativeQuantity())

    seen: set[type[object]] = set()
    for lines in bill_categories:
        for line in lines:
            item_type: type[object] = type(line.item)
            if item_type in seen:
                return Err(error=BillingError_DuplicateItem())
            seen.add(item_type)

    for line in medical:
        if not isinstance(line.item, medical_items):
            return Err(error=BillingError_WrongCategory())
    for line in grocery:
        if not isinstance(line.item, grocery_items):
            return Err(error=BillingError_WrongCategory())
    for line in drinks:
        if not isinstance(line.item, drinks_items):
            return Err(error=BillingError_WrongCategory())

    def medical_subtotal(lines: CottList[Quantity]) -> int:
        subtotal: int = 0
        for line in lines:
            if isinstance(line.item, BillingItem_Sanitizer):
                unit_price: int = 200
            elif isinstance(line.item, BillingItem_Mask):
                unit_price = 500
            elif isinstance(line.item, BillingItem_HandGloves):
                unit_price = 1200
            elif isinstance(line.item, BillingItem_Dettol):
                unit_price = 3000
            elif isinstance(line.item, BillingItem_Newsprin):
                unit_price = 500
            else:
                unit_price = 1500
            subtotal += line.quantity * unit_price
        return subtotal

    def grocery_subtotal(lines: CottList[Quantity]) -> int:
        subtotal: int = 0
        for line in lines:
            if isinstance(line.item, BillingItem_Rice):
                unit_price: int = 1000
            elif isinstance(line.item, BillingItem_FoodOil):
                unit_price = 1000
            elif isinstance(line.item, BillingItem_Wheat):
                unit_price = 1000
            elif isinstance(line.item, BillingItem_Daal):
                unit_price = 600
            elif isinstance(line.item, BillingItem_Flour):
                unit_price = 800
            else:
                unit_price = 500
            subtotal += line.quantity * unit_price
        return subtotal

    def drinks_subtotal(lines: CottList[Quantity]) -> int:
        subtotal: int = 0
        for line in lines:
            if isinstance(line.item, BillingItem_Sprite):
                unit_price: int = 1000
            elif isinstance(line.item, BillingItem_Limka):
                unit_price = 1000
            elif isinstance(line.item, BillingItem_Mazza):
                unit_price = 1000
            elif isinstance(line.item, BillingItem_Coke):
                unit_price = 1000
            elif isinstance(line.item, BillingItem_Fanta):
                unit_price = 1000
            else:
                unit_price = 1000
            subtotal += line.quantity * unit_price
        return subtotal

    def rounded_percent(cents: int, percent: int) -> int:
        quotient: int
        remainder: int
        quotient, remainder = divmod(cents * percent, 100)
        if remainder > 50 or (remainder == 50 and quotient % 2 == 1):
            return quotient + 1
        return quotient

    medical_cents: int = medical_subtotal(medical)
    grocery_cents: int = grocery_subtotal(grocery)
    drinks_cents: int = drinks_subtotal(drinks)
    medical_tax_cents: int = rounded_percent(medical_cents, 5)
    grocery_tax_cents: int = rounded_percent(grocery_cents, 5)
    drinks_tax_cents: int = rounded_percent(drinks_cents, 10)
    total_cents: int = medical_cents + grocery_cents + drinks_cents + medical_tax_cents + grocery_tax_cents + drinks_tax_cents
    return Ok(
        value=BillTotals(
            medical_subtotal=medical_cents / 100,
            grocery_subtotal=grocery_cents / 100,
            drinks_subtotal=drinks_cents / 100,
            medical_tax=medical_tax_cents / 100,
            grocery_tax=grocery_tax_cents / 100,
            drinks_tax=drinks_tax_cents / 100,
            total=total_cents / 100,
        )
    )
