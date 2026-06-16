from backend.sources.base import BaseSource
from backend.models.technology import Technology

# India TIFAC — Technology Information, Forecasting and Assessment Council
# No public search API available. Listed as a Search redirect source so users
# know the platform exists and can follow the external link to search directly.


class IndiaTIFACSource(BaseSource):
    id = "india_tifac"
    name = "India TIFAC TechMonitor"
    country = "India"
    institution = "Technology Information, Forecasting and Assessment Council (TIFAC)"
    status = "Search redirect"
    url = "https://tifac.org.in/techmonitor"
    ttl_seconds = 86400

    async def search(self, query: str, filters: dict) -> list[Technology]:
        return []

    def is_healthy(self) -> bool:
        return True
