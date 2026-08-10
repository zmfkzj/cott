from cott_runtime import CottList, Err, Ok, Result, UNIT, Unit
from curriculum.billing_system_types import BillingError, BillingError_DuplicateItem, BillingError_NegativeQuantity, BillingError_WrongCategory, BillingItem_Coke, BillingItem_Daal, BillingItem_Dettol, BillingItem_Fanta, BillingItem_Flour, BillingItem_FoodOil, BillingItem_HandGloves, BillingItem_Limka, BillingItem_Maggi, BillingItem_Mask, BillingItem_MountainDuo, BillingItem_Mazza, BillingItem_Newsprin, BillingItem_Rice, BillingItem_Sanitizer, BillingItem_Sprite, BillingItem_ThermalGun, BillingItem_Wheat, Quantity


def validate_bill_lines(medical: CottList[Quantity], grocery: CottList[Quantity], drinks: CottList[Quantity]) -> Result[Unit, BillingError]:
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

    return Ok(value=UNIT)
