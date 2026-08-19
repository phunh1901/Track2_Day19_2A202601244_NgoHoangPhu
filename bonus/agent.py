"""Hybrid Memory Agent combining Vector Store (Episodic) and Feast Feature Store (Profile & Activity)."""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.embeddings import Embedder  # noqa: E402

logger = logging.getLogger(__name__)


class HybridMemoryAgent:
    """Agent that manages episodic memory in Qdrant and user profile/velocity in Feast."""

    COLLECTION_NAME = "agent_episodic_memory"

    def __init__(self, embedder: Embedder | None = None) -> None:
        self.embedder = embedder or Embedder()
        self.client = QdrantClient(location=":memory:")
        self._init_collection()
        self._memory_counter = 0

        # Lazy feast store initialization
        self._feast_store: Any = None
        self._init_feast()

    def _init_collection(self) -> None:
        """Create an in-memory collection with payload index on user_id."""
        self.client.recreate_collection(
            collection_name=self.COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(
                size=self.embedder.dim,
                distance=qmodels.Distance.COSINE,
            ),
        )

    def _init_feast(self) -> None:
        """Attempt to connect to local Feast feature store if registry exists."""
        feast_repo_path = ROOT / "app" / "feast_repo"
        if (feast_repo_path / "feature_store.yaml").exists():
            try:
                from feast import FeatureStore

                self._feast_store = FeatureStore(repo_path=str(feast_repo_path))
            except Exception as e:
                logger.warning(f"Feast not initialized, fallback to simulated features: {e}")
                self._feast_store = None

    def remember(self, text: str, user_id: str = "u_001", metadata: dict[str, Any] | None = None) -> None:
        """Add a new piece of episodic memory for a specific user.

        1. Chunk text (simple sentence/paragraph split).
        2. Embed each chunk using Embedder.
        3. Upsert into Qdrant with payload: user_id, timestamp, text, metadata.
        """
        meta = metadata or {}
        chunks = [c.strip() for c in text.split("\n") if c.strip()]
        if not chunks:
            chunks = [text.strip()]

        for chunk in chunks:
            self._memory_counter += 1
            vector = next(self.embedder.embed([chunk])).tolist()
            payload = {
                "user_id": user_id,
                "text": chunk,
                "created_at": time.time(),
                **meta,
            }
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[
                    qmodels.PointStruct(
                        id=self._memory_counter,
                        vector=vector,
                        payload=payload,
                    )
                ],
            )

    def _get_user_features(self, user_id: str) -> dict[str, Any]:
        """Fetch stable profile and recent velocity features from Feast or fallback defaults."""
        defaults = {
            "topic_affinity": "cloud",
            "reading_speed_wpm": 220,
            "preferred_lang": "vi-VN",
            "queries_last_hour": 14,
            "distinct_topics_last_hour": 3,
        }

        if self._feast_store is not None:
            try:
                response = self._feast_store.get_online_features(
                    features=[
                        "user_profile_features:topic_affinity",
                        "user_profile_features:reading_speed_wpm",
                        "query_velocity_features:queries_last_hour",
                        "query_velocity_features:distinct_topics_last_hour",
                    ],
                    entity_rows=[{"user_id": user_id}],
                ).to_dict()

                topic = response.get("topic_affinity", [None])[0]
                speed = response.get("reading_speed_wpm", [None])[0]
                q_hour = response.get("queries_last_hour", [None])[0]
                topics_hour = response.get("distinct_topics_last_hour", [None])[0]

                if topic is not None:
                    defaults["topic_affinity"] = str(topic)
                if speed is not None:
                    defaults["reading_speed_wpm"] = int(speed)
                if q_hour is not None:
                    defaults["queries_last_hour"] = int(q_hour)
                if topics_hour is not None:
                    defaults["distinct_topics_last_hour"] = int(topics_hour)
            except Exception as e:
                logger.debug(f"Feast lookup fallback for {user_id}: {e}")

        return defaults

    def recall(self, query: str, user_id: str = "u_001", top_k: int = 3) -> str:
        """Retrieve top-K episodic memories + user profile features -> assembled prompt context."""
        # 1. Fetch user features from Feast
        features = self._get_user_features(user_id)

        # 2. Vector search filtered by user_id
        q_vec = next(self.embedder.embed([query])).tolist()
        search_filter = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="user_id",
                    match=qmodels.MatchValue(value=user_id),
                )
            ]
        )

        res = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=q_vec,
            query_filter=search_filter,
            limit=top_k,
        )

        memories = [f"- {p.payload.get('text')} (relevance: {p.score:.3f})" for p in res.points if p.payload]
        memories_text = "\n".join(memories) if memories else "No relevant past episodic memories found."

        # 3. Assemble rich context prompt
        context = (
            f"[User Profile (Feast Feature Store)]\n"
            f"  - User ID: {user_id}\n"
            f"  - Topic Affinity: {features['topic_affinity']}\n"
            f"  - Reading Speed: {features['reading_speed_wpm']} wpm | Preferred Language: {features['preferred_lang']}\n"
            f"  - Recent Activity: {features['queries_last_hour']} queries in past hour across {features['distinct_topics_last_hour']} topics\n"
            f"\n"
            f"[Retrieved Episodic Memories (Qdrant Vector Store - Top {len(res.points)})]\n"
            f"{memories_text}\n"
            f"\n"
            f"[Current Query]\n"
            f"  \"{query}\""
        )
        return context
