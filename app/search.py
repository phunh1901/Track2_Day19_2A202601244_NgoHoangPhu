"""Searcher — keyword (BM25) + semantic (vector) + hybrid (RRF) on the lab corpus.

Designed to work in both lite (Qdrant in-memory) and docker (Qdrant server) modes;
switch via env var QDRANT_MODE=memory|server (defaults to memory).

The hybrid mode uses Reciprocal Rank Fusion with k=60 — the same default used
by Vespa, Elasticsearch, and the hybrid RAG production stacks in the deck §3.
"""
from __future__ import annotations

import json
import hashlib
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from rank_bm25 import BM25Okapi

from app.embeddings import Embedder

Mode = Literal["keyword", "semantic", "hybrid"]
# Model + dimension now come from EMBEDDING_BACKEND (see app/embeddings.py).
# Defaults are unchanged: fastembed / BAAI/bge-small-en-v1.5 / 384-dim.
EMBED_MODEL = Embedder().model_name
EMBED_DIM = Embedder().dim
COLLECTION = "lab19_corpus"


@dataclass
class SearchHit:
    doc_id: str
    title: str
    text: str
    score: float

    def dict(self) -> dict:
        return {"doc_id": self.doc_id, "title": self.title, "text": self.text, "score": self.score}


class Searcher:
    """Holds the BM25 index, Qdrant client, and document metadata.

    Construction is deliberately heavy (loading the embedding model + indexing
    the whole corpus once); callers should reuse a single instance.
    """

    def __init__(self) -> None:
        self.docs: list[dict] = []
        self.doc_ids: list[str] = []
        self.bm25: BM25Okapi | None = None
        self.client: QdrantClient | None = None
        self.embedder: Embedder | None = None
        self.corpus_path: Path | None = None

    @property
    def size(self) -> int:
        return len(self.docs)

    @classmethod
    def from_corpus(cls, corpus_path: Path) -> "Searcher":
        # A student who opens NB1 before running setup otherwise gets a bare
        # FileNotFoundError pointing at a relative path, with no hint that the
        # corpus is generated rather than committed.
        if not Path(corpus_path).exists():
            raise FileNotFoundError(
                f"Corpus not found at {corpus_path}.\n"
                "The corpus is generated, not committed. Run:\n"
                "    bash setup-lite.sh      # first time (venv + deps + data)\n"
                "    make seed               # if you only need to regenerate data"
            )
        s = cls()
        s.corpus_path = Path(corpus_path).resolve()
        s._load_docs(corpus_path)
        s._build_bm25()
        s._build_vector_index()
        return s

    # ── ingestion ───────────────────────────────────────────────────────
    def _load_docs(self, corpus_path: Path) -> None:
        with corpus_path.open(encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                self.docs.append(d)
                self.doc_ids.append(d["doc_id"])

    def _build_bm25(self) -> None:
        # Tokenise on whitespace — for VN+EN mixed text this is "good enough" baseline.
        # A real production system would use a proper VN tokenizer (underthesea / pyvi).
        # That choice is a "think hard" decision flagged in VIBE-CODING.md.
        tokenized = [self._tokenize(d["title"] + " " + d["text"]) for d in self.docs]
        self.bm25 = BM25Okapi(tokenized)

    def _build_vector_index(self) -> None:
        self.embedder = Embedder()

        mode = os.getenv("QDRANT_MODE", "memory")
        if mode == "server":
            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            self.client = QdrantClient(url=url)
        else:
            self.client = QdrantClient(":memory:")

        # Recreate is OK in lite mode (it's in-memory); for server, only create if missing.
        existing = {c.name for c in self.client.get_collections().collections}
        if COLLECTION in existing and mode == "server":
            self.client.delete_collection(COLLECTION)
        self.client.create_collection(
            collection_name=COLLECTION,
            # dimension must follow the chosen model, not a module constant --
            # switching EMBEDDING_BACKEND changes it (384 -> 1024 -> 1536).
            vectors_config=VectorParams(size=self.embedder.dim, distance=Distance.COSINE),
        )

        vectors = self._load_or_build_document_vectors()

        # Upsert in batches of 64. Embeddings are cached separately because a
        # Qdrant in-memory collection must be recreated in every process.
        BATCH = 64
        points: list[PointStruct] = []
        for start in range(0, len(self.docs), BATCH):
            batch = self.docs[start:start + BATCH]
            for i, d in enumerate(batch):
                v = vectors[start + i]
                points.append(PointStruct(
                    id=start + i,
                    vector=v.tolist(),
                    payload={"doc_id": d["doc_id"], "title": d["title"], "text": d["text"]},
                ))
        self.client.upsert(collection_name=COLLECTION, points=points)

    def _load_or_build_document_vectors(self) -> np.ndarray:
        """Return corpus vectors from a model-safe cache or compute them.

        The key includes corpus bytes, backend, model name and dimension. A
        model/corpus change therefore cannot reuse vectors from another space;
        it creates a new cache file and re-embeds the entire corpus.
        """
        assert self.embedder is not None and self.corpus_path is not None
        digest = hashlib.sha256()
        digest.update(self.corpus_path.read_bytes())
        digest.update(self.embedder.backend.encode())
        digest.update(self.embedder.model_name.encode())
        digest.update(str(self.embedder.dim).encode())
        cache_dir = self.corpus_path.parent / ".embedding_cache"
        cache_dir.mkdir(exist_ok=True)
        cache_path = cache_dir / f"documents-{digest.hexdigest()[:20]}.npy"

        if cache_path.exists():
            cached = np.load(cache_path, allow_pickle=False)
            if cached.shape == (len(self.docs), self.embedder.dim):
                return np.asarray(cached, dtype=np.float32)

        batches: list[np.ndarray] = []
        batch_size = 64
        for start in range(0, len(self.docs), batch_size):
            batch = self.docs[start:start + batch_size]
            texts = [d["title"] + " " + d["text"] for d in batch]
            batches.append(np.asarray(list(self.embedder.embed(texts)), dtype=np.float32))
        vectors = np.vstack(batches)
        if vectors.shape != (len(self.docs), self.embedder.dim):
            raise ValueError(f"unexpected document vector shape: {vectors.shape}")

        tmp_path = cache_path.with_suffix(".tmp.npy")
        np.save(tmp_path, vectors, allow_pickle=False)
        os.replace(tmp_path, cache_path)
        return vectors

    # ── retrieval ───────────────────────────────────────────────────────
    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return text.lower().split()

    def search(
        self,
        query: str,
        mode: Mode = "hybrid",
        top_k: int = 10,
        rrf_k: int = 60,
    ) -> list[SearchHit]:
        if mode == "keyword":
            return self._search_keyword(query, top_k)
        if mode == "semantic":
            return self._search_semantic(query, top_k)
        if mode == "hybrid":
            return self._search_hybrid(query, top_k, rrf_k)
        raise ValueError(f"unknown mode {mode!r}")

    def _search_keyword(self, query: str, top_k: int) -> list[SearchHit]:
        assert self.bm25 is not None
        scores = self.bm25.get_scores(self._tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]
        return [
            SearchHit(
                doc_id=self.docs[i]["doc_id"],
                title=self.docs[i]["title"],
                text=self.docs[i]["text"],
                score=float(scores[i]),
            )
            for i in ranked
        ]

    def _search_semantic(self, query: str, top_k: int) -> list[SearchHit]:
        assert self.client is not None and self.embedder is not None
        q_vec = list(self._embed_query(query))
        result = self.client.query_points(
            collection_name=COLLECTION,
            query=q_vec,
            limit=top_k,
        )
        return [
            SearchHit(
                doc_id=p.payload["doc_id"],
                title=p.payload["title"],
                text=p.payload["text"],
                score=float(p.score),
            )
            for p in result.points
        ]

    @lru_cache(maxsize=1024)
    def _embed_query(self, query: str) -> tuple[float, ...]:
        """Embed a query once per Searcher instance.

        Query embedding dominated P99 on the reference Windows CPU (~70 ms).
        A bounded cache is safe because the embedding backend is immutable for
        the lifetime of a Searcher. Rebuilding the Searcher after a model swap
        creates a fresh cache and a fresh vector collection, so vectors from
        different embedding spaces can never be mixed.
        """
        assert self.embedder is not None
        return tuple(float(x) for x in next(self.embedder.embed([query])))

    def _search_hybrid(self, query: str, top_k: int, rrf_k: int) -> list[SearchHit]:
        # Pull a deeper top-K from each retriever so RRF has signal beyond top-10.
        depth = max(top_k * 5, 50)
        kw_hits = self._search_keyword(query, depth)
        sem_hits = self._search_semantic(query, depth)

        # Reciprocal Rank Fusion — score(d) = sum over rankers of 1 / (k + rank_r(d))
        # rank_r is 1-based (first position is rank 1, not 0).
        rrf_scores: dict[str, float] = {}
        meta: dict[str, SearchHit] = {}
        for hits in (kw_hits, sem_hits):
            for rank, h in enumerate(hits, start=1):
                rrf_scores[h.doc_id] = rrf_scores.get(h.doc_id, 0.0) + 1.0 / (rrf_k + rank)
                meta.setdefault(h.doc_id, h)

        ordered = sorted(rrf_scores.items(), key=lambda kv: -kv[1])[:top_k]
        return [
            SearchHit(
                doc_id=doc_id,
                title=meta[doc_id].title,
                text=meta[doc_id].text,
                score=score,
            )
            for doc_id, score in ordered
        ]
