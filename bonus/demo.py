"""Demo script executing 5 distinct queries showcasing Hybrid Memory (Vector + Feature Store)."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bonus.agent import HybridMemoryAgent


def main() -> int:
    print("=" * 70)
    print("DEMO: Hybrid Memory Assistant (Vector Episodic + Feast Profile)")
    print("=" * 70)

    agent = HybridMemoryAgent()

    # Seed some episodic memories for user u_001
    print("\n[Ingesting Episodic Memories for user u_001]...")
    sample_memories = [
        "Đã đọc bài báo về Kubernetes Cluster Autoscaler và tối ưu chi phí hạ tầng trên AWS EKS.",
        "Ghi chú: Cần áp dụng Istio Service Mesh cho việc mTLS giữa các microservices.",
        "Đã nghiên cứu cơ chế bảo mật Cloud Security IAM và nguyên tắc Least Privilege.",
        "Đã hoàn thành khóa học Machine Learning Feature Engineering và Feature Store với Feast.",
        "Lưu tài liệu: Best practices triển khai Qdrant Vector Database cho bài toán RAG Tiếng Việt.",
    ]
    for mem in sample_memories:
        agent.remember(mem, user_id="u_001")
    print(f"-> Ingested {len(sample_memories)} memories successfully.\n")

    queries = [
        (
            1,
            "Hỏi đơn giản (chỉ vector hit)",
            "Tôi đã đọc gì về Kubernetes?",
        ),
        (
            2,
            "Hỏi cần profile context (topic affinity)",
            "Recommend cho tôi nên đọc tài liệu gì tiếp theo phù hợp với sở thích?",
        ),
        (
            3,
            "Hỏi cần fresh activity (queries velocity)",
            "Tôi đang quan tâm và tìm kiếm những gì nhiều nhất gần đây?",
        ),
        (
            4,
            "Hỏi paraphrase (vector semantic match)",
            "Tài liệu hướng dẫn về tự động mở rộng quy mô hạ tầng máy chủ?",
        ),
        (
            5,
            "Hỏi mixed (kết hợp episodic + profile context)",
            "Cho tôi bản tóm tắt về cloud security và đề xuất bước tiếp theo",
        ),
    ]

    for q_id, q_type, q_text in queries:
        print("-" * 70)
        print(f"QUERY {q_id}: [{q_type}]")
        print(f"Input: \"{q_text}\"")
        context = agent.recall(q_text, user_id="u_001", top_k=2)
        print("\n--- ASSEMBLED CONTEXT FOR LLM ---")
        print(context)
        print("-" * 70 + "\n")

    print("=" * 70)
    print("All 5 queries executed successfully. POC Demo finished with exit code 0.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
