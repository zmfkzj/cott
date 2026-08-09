from cott_runtime import Ok, Result
from curriculum.address_validation_types import Address, AddressError


def run() -> Result[Address, AddressError]:
    return Ok(value=Address(line1="1 Main St", city="Seoul", postal_code="12345"))
