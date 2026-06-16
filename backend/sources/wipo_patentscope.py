import httpx
from datetime import datetime

from backend.sources.base import BaseSource
from backend.models.technology import Technology

# WIPO PATENTSCOPE REST API — free, no key required
# Docs: https://patentscope.wipo.int/search/en/help/data_download.jsf
# Search endpoint returns JSON with patent metadata in English


class WIPOPatentscopeSource(BaseSource):
    id = "wipo_patentscope"
    name = "WIPO PATENTSCOPE"
    country = "International (AP focus)"
    institution = "World Intellectual Property Organization (WIPO)"
    status = "Metadata search"
    url = "https://patentscope.wipo.int"
    ttl_seconds = 86400

    _search_url = "https://patentscope.wipo.int/search/en/rest/patentscope/search/en/AP"

    def _normalize(self, item: dict) -> Technology:
        doc_id = item.get("id", "")
        title = item.get("en_title") or item.get("title") or "Untitled"
        summary = item.get("en_abstract") or item.get("abstract") or ""
        ipc_codes = item.get("ipcCode", "")
        sector = ipc_codes.split(";")[0].strip() if ipc_codes else "Patents"
        applicant = item.get("applicantName") or item.get("applicant") or ""
        pub_date = item.get("publicationDate") or item.get("pubDate") or ""
        country_code = item.get("officeCode") or ""
        keywords_raw = item.get("en_claims") or ""
        keywords = [w.strip() for w in ipc_codes.split(";") if w.strip()][:8]

        tech_url = f"https://patentscope.wipo.int/search/en/detail.jsf?docId={doc_id}" if doc_id else self.url

        return Technology(
            id=f"wipo_{doc_id}",
            title=title,
            summary=summary[:1000] if summary else "",
            sector=sector,
            language="English",
            keywords=keywords,
            country=country_code or "International",
            source_id=self.id,
            source_name=self.name,
            url=tech_url,
            fetched_at=datetime.utcnow(),
            org_name=applicant,
            transfer_type="Patent",
            dev_status="",
            reg_date=pub_date,
            sub_sector=ipc_codes,
        )

    async def search(self, query: str, filters: dict) -> list[Technology]:
        if not query:
            return []

        params = {
            "query": query,
            "office": "AP",
            "pageSize": "15",
            "lang": "EN",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    "https://patentscope.wipo.int/search/en/rest/patentscope/search/en",
                    params=params,
                    headers={"Accept": "application/json"},
                )
                r.raise_for_status()
                data = r.json()
        except Exception:
            return []

        results = data.get("results") or data.get("patents") or []
        if not isinstance(results, list):
            return []

        return [self._normalize(item) for item in results if isinstance(item, dict)]

    def is_healthy(self) -> bool:
        return True
