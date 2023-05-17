"""Constants."""

from .backports.enum import StrEnum


class Brand(StrEnum):
    AUGUST = "august"
    YALE_ACCESS = "yale_access"
    YALE_HOME = "yale_home"


DEFAULT_BRAND = Brand.AUGUST

BASE_URLS = {
    Brand.AUGUST: "https://api-production.august.com",
    Brand.YALE_ACCESS: "https://api-production.august.com",
    Brand.YALE_HOME: "https://api.aaecosystem.com",
}

BRANDS = {
    Brand.AUGUST: "August",
    Brand.YALE_ACCESS: "Yale Access",
    Brand.YALE_HOME: "Yale Home",
}
