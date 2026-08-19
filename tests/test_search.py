"""Strict guards for the core rubric's silent-failure cases."""
from __future__ import annotations

import pytest

from app.search import SearchHit, Searcher


def _hit(doc_id: str) -> SearchHit:
    return SearchHit(doc_id=doc_id, title=doc_id, text="", score=0.0)


def test_rrf_uses_one_based_rank_and_k_constant(monkeypatch):
    """Lock the rubric formula: sum 1/(k + rank), with rank starting at 1."""
    searcher = Searcher()
    kw = [_hit("shared"), _hit("kw_only")]
    sem = [_hit("sem_only"), _hit("shared")]
    monkeypatch.setattr(searcher, "_search_keyword", lambda query, depth: kw)
    monkeypatch.setattr(searcher, "_search_semantic", lambda query, depth: sem)

    out = searcher._search_hybrid("q", top_k=3, rrf_k=60)
    by_id = {hit.doc_id: hit.score for hit in out}

    assert out[0].doc_id == "shared"
    assert by_id["shared"] == pytest.approx(1 / 61 + 1 / 62)
    assert by_id["kw_only"] == pytest.approx(1 / 62)
    assert by_id["sem_only"] == pytest.approx(1 / 61)


def test_hybrid_pulls_depth_fifty_from_each_retriever(monkeypatch):
    searcher = Searcher()
    depths: list[int] = []

    def fake(query, depth):
        depths.append(depth)
        return []

    monkeypatch.setattr(searcher, "_search_keyword", fake)
    monkeypatch.setattr(searcher, "_search_semantic", fake)
    assert searcher._search_hybrid("q", top_k=10, rrf_k=60) == []
    assert depths == [50, 50]


def test_search_response_exposes_server_latency_field():
    from app.main import SearchResponse

    fields = SearchResponse.model_fields
    assert "latency_ms" in fields
    assert "Server-side" in (fields["latency_ms"].description or "")


def test_query_embedding_cache_is_bounded_and_reuses_vectors():
    class CountingEmbedder:
        def __init__(self):
            self.calls = 0

        def embed(self, texts):
            self.calls += 1
            yield [0.1, 0.2, 0.3]

    searcher = Searcher()
    searcher.embedder = CountingEmbedder()
    assert searcher._embed_query("same") == searcher._embed_query("same")
    assert searcher.embedder.calls == 1
    assert searcher._embed_query.cache_info().maxsize == 1024
