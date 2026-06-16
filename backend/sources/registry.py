from backend.sources.korea_ntb import KoreaNTBSource
from backend.sources.wipo_patentscope import WIPOPatentscopeSource
from backend.sources.india_tifac import IndiaTIFACSource

SOURCES = [
    KoreaNTBSource(),
    WIPOPatentscopeSource(),
    IndiaTIFACSource(),
]

SOURCE_MAP = {s.id: s for s in SOURCES}
