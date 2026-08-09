from cott_runtime import Ok
from curriculum.address_validation_types import Address


def run() -> Ok[Address]:
    return Ok(value=Address(line1="1 Main St", city="Seoul", postal_code="12345"))
