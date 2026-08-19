# Reflection — Lab 19

**Tên:** Ngô Hoàng Phú  
**Cohort:** 2A202601244  
**Path đã chạy:** lite  

---

## Câu hỏi (≤ 200 chữ)

> Trên golden set 50 queries, mode nào thắng ở loại query nào (`exact` /
> `paraphrase` / `mixed`), và tại sao? Khi nào bạn **không** dùng hybrid
> (i.e. khi nào pure BM25 hoặc pure vector là lựa chọn đúng)?

Thực nghiệm trên 50 golden queries:
- **`mixed` (20 queries):** **Hybrid (RRF k=60) thắng tuyệt đối (100.0%)**, vượt trội BM25 (97.0%) và Semantic (98.5%) nhờ kết hợp khớp từ khóa chính xác và mở rộng ngữ nghĩa.
- **`exact` (15 queries):** **BM25 đạt 96.7%**, bằng Hybrid và hơn Semantic (88.7%) do TF-IDF bắt trúng thuật ngữ đặc thù.
- **`paraphrase` (15 queries):** Semantic và Hybrid duy trì gom đúng cụm chủ đề tốt hơn khi câu hỏi bị thay đổi từ vựng.
- **Trung bình chung:** Hybrid dẫn đầu (78.6% vs BM25 77.8% vs Vector 73.2%).

**Khi nào KHÔNG dùng Hybrid:**
1. *Pure BM25:* Dùng khi tra cứu mã lỗi, mã SKU, ID, tên hàm code cụ thể hoặc hệ thống cần tối giản chi phí, không thể chạy model embedding.
2. *Pure Vector:* Dùng cho tìm kiếm trừu tượng, đa ngữ (cross-lingual), hoặc tìm kiếm đa phương tiện (image-to-text) nơi không có từ khóa trùng khớp.

---

## Điều ngạc nhiên nhất khi làm lab này

Sự sụt giảm nghiêm trọng của Recall trong Filtered Search khi Post-filtering bị quá chọn lọc (tụt về 0% ở mức 4%), và cách Filtered-ANN trong Qdrant duy trì Recall 1.00 hoàn hảo.

---

## Bonus challenge

- [x] Đã làm bonus (xem `bonus/`)
- [ ] Pair work với: _N/A_
