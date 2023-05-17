"""Constants."""

from .backports.enum import StrEnum


class Brand(StrEnum):
    august = "august"
    yale_access = "yale_access"
    yale_home = "yale_home"


DEFAULT_BRAND = Brand.august

BASE_URLS = {
    Brand.august: "https://api-production.august.com",
    Brand.yale_access: "https://api-production.august.com",
    Brand.yale_home: "https://api.aaecosystem.com",
}

BRANDS = {
    Brand.august: "August",
    Brand.yale_access: "Yale Access",
    Brand.yale_home: "Yale Home",
}
