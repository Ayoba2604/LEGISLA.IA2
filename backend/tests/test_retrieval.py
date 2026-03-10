from backend.app.schemas.retrieval import RetrievalFilters
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.source_catalog import SourceCatalog


def test_hybrid_retrieval_returns_results():
    catalog = SourceCatalog()
    catalog.load_bootstrap_sources()
    service = RetrievalService(catalog)

    results = service.search("compra com defeito", top_k=3, filters=RetrievalFilters())

    assert results
    assert results[0].chunk.title
    assert results[0].final_score >= 0

