# Kế hoạch hoàn thành Lab 19 theo rubric — mục tiêu 170/170

## 1. Mục tiêu và chiến lược

Kế hoạch này nhắm toàn bộ số điểm được liệt kê trong `rubric.md`:

- **Core NB1–NB4: 100/100**.
- **Advanced NB5–NB8: 50/50**.
- **Bonus Challenge: 20/20**.
- **Tổng mục tiêu: 170/170 điểm rubric**. Nếu lớp chỉ chấm core hoặc chỉ chọn
  một phần advanced, các phần tương ứng vẫn độc lập và đầy đủ bằng chứng.

Chọn **Lite path trong WSL/Linux** làm đường chạy chính vì rubric chấp nhận
Lite và Docker như nhau, Lite ít phụ thuộc dịch vụ, dễ tái lập và phù hợp nhất
để giữ latency ổn định. Chỉ chuyển embedding model/Docker khi kết quả thực đo
không đạt; không đổi stack theo cảm tính.

## 2. State hiện tại sau khi audit repo

Thời điểm audit: **2026-08-19**.

### Những gì đã có

- Git đang ở branch `main`, worktree sạch, đã có remote `origin` trỏ tới repo
  GitHub của học viên.
- Source cho 8 notebook dạng Jupytext `.py` đã có.
- Code core đã có sẵn: embedding/index, BM25, semantic search, RRF hybrid,
  FastAPI và 3 Feast feature views.
- Code advanced đã có sẵn: filtered search, agentic retrieval, semantic cache,
  feature engineering và test tương ứng.
- Các đoạn mang nhãn `TODO` trong NB1–NB4 thực tế đã có implementation bên
  dưới; phần còn thiếu chính là chạy, xác minh, sửa khi metric không đạt và lưu
  bằng chứng.

### Những gì chưa có hoặc đang chặn điểm

- Máy Windows hiện **không có Python cài đặt** (`py` launcher có nhưng không
  tìm thấy interpreter); `python` và `python3` đều không tồn tại.
- Chưa có `.venv`, `.env`, corpus/golden set, agent queries, Feast data,
  registry hoặc online store.
- Chưa có notebook `.ipynb` và output cell đã chạy.
- Chưa có `submission/screenshots/` và chưa có ảnh bằng chứng.
- `submission/REFLECTION.md` vẫn là template, chưa điền tên/cohort/path/câu trả
  lời.
- Chưa có thư mục `bonus/`.
- **Lỗi test discovery:** `pyproject.toml` đặt `testpaths = ["app", "scripts"]`
  nhưng test thật nằm trong `tests/`. Nếu giữ nguyên, `make test` không chạy bộ
  test mà rubric yêu cầu.
- Pin `pyarrow` trong `pyproject.toml` là `<22`, không đồng bộ với
  `requirements.txt` là `<26`; đây là rủi ro tái lập trên Python mới.
- Script/Makefile dùng layout Unix `.venv/bin/...`; chạy trực tiếp bằng
  PowerShell/Windows Python sẽ không khớp. Vì vậy dùng WSL xuyên suốt.

**Kết luận state:** code scaffold gần hoàn chỉnh nhưng **evidence-ready score
hiện tại là 0/170**, vì grader chấm output notebook + screenshot + khả năng tái
lập, không chỉ chấm source tồn tại.

## 3. Ma trận rubric và bằng chứng phải nộp

| Khối | Điểm | State hiện tại | Bằng chứng bắt buộc để khóa điểm |
|---|---:|---|---|
| NB1 | 20 | Code index/search đã có; chưa chạy | `Indexed: 1000`, top-5 keyword, top-5 paraphrase chủ yếu `cloud` |
| NB2 | 25 | RRF đúng công thức trong source; chưa có metric | Code rank 1-based, bảng avg hybrid > cả hai mode, bảng slice |
| NB3 | 25 | API/schema đã có; chưa benchmark | Response có `latency_ms`, bảng 3 mode, hybrid P99 server < 50 ms |
| NB4 | 25 | Có 3 feature views; chưa apply/materialize | apply thấy 3 views, materialize log, online dict, P99 < 10 ms, PIT 3 dòng |
| Repro core | 5 | Chưa có runtime | clean setup + benchmark exit 0 |
| NB5 | 10 | Source đã có; chưa chạy | recall/selectivity table và over-fetch ladder |
| NB6 | 12 | Source đã có; thiếu generated query/output/Feast state | fair budget=16 table, giải thích filter, `build_context()` có feature + doc IDs |
| NB7 | 12 | Source đã có; chưa chạy | threshold sweep 2 cột, chọn threshold, leak rồi namespace fix |
| NB8 | 12 | Source đã có; chưa chạy | leakage gap, PIT/latest %, AUC gap, ODFV hai amount |
| Test/verify advanced | 4 | Test discovery đang sai | toàn bộ test thật pass và `verify-lite` pass |
| Bonus | 20 | Chưa có | architecture ≥600 từ + diagram + tradeoff; agent/demo chạy được |

## 4. Kế hoạch thực hiện chi tiết

### Bước 0 — Chốt baseline và quy tắc không làm mất bài

**State hiện tại**

- Branch `main`, worktree sạch; chưa có artifact do học viên tạo.

**Cần làm**

- Ghi nhận baseline trước khi sửa và làm theo từng commit nhỏ.
- Không commit `.env`, `.venv`, registry, online-store DB hoặc model cache.

**Làm như nào**

```bash
git status --short
git branch --show-current
git remote -v
git switch -c lab19-max-score
```

Sau mỗi mission: `git diff --check`, xem diff, rồi commit riêng. Branch có thể
đổi tên, nhưng không nên làm trực tiếp một commit khổng lồ trên `main`.

**Làm ở đâu**

- Terminal WSL, tại root repo.

**Output cần đạt**

- Có branch làm bài riêng, `git status` rõ ràng, không có secret/artifact runtime
  bị track nhầm.

---

### Bước 1 — Dựng runtime Linux tái lập được

**State hiện tại**

- Windows chưa có Python; script setup yêu cầu `python3` và `.venv/bin`.

**Cần làm**

- Cài/khởi động WSL Ubuntu và dùng Python **3.10–3.13**. Khuyến nghị Python
  3.12/3.13; tránh 3.14 nếu không cần vì Feast/dill có nhánh override riêng.

**Làm như nào**

Trong WSL:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip make git
python3 --version
git --version
make --version
cd /mnt/c/Users/HP/Desktop/AI_Vin/Labs/Lab19/Day19-Track2-VectorFeatureStore-Lab-NgoHoangPhu-2A202601244
```

Nếu `python3 --version` thấp hơn 3.10 thì cài một bản 3.10–3.13 trước khi đi
tiếp. Không trộn PowerShell Python với WSL venv.

**Làm ở đâu**

- WSL Ubuntu; repo vẫn nằm tại ổ C và được truy cập qua `/mnt/c/...`.

**Output cần đạt**

- `python3 --version` trả về 3.10–3.13.
- `bash`, `make`, `git` chạy được trong cùng một environment.

---

### Bước 2 — Sửa các blocker tĩnh trước khi setup

**State hiện tại**

- Pytest không discover thư mục `tests/`.
- `pyarrow` pin giữa hai manifest không đồng bộ.
- NB1–NB4 vẫn ghi `TODO` dù code đã được điền, dễ tạo cảm giác submission chưa
  hoàn thành.

**Cần làm**

1. Trong `pyproject.toml`, đổi `testpaths` thành `['tests']`.
2. Đồng bộ `pyarrow>=17,<26` trong `pyproject.toml` với `requirements.txt`.
3. Đổi heading/comment `TODO` thành `Implementation` hoặc `Exercise completed`
   trong NB1–NB4; giữ nguyên logic đã đúng.
4. Không sửa test chỉ để ép pass; nếu test fail thì sửa implementation.

**Làm như nào**

- Sửa tối thiểu, review bằng:

```bash
git diff -- pyproject.toml notebooks/
git diff --check
```

**Làm ở đâu**

- `pyproject.toml`.
- `notebooks/01_embeddings_index.py` đến
  `notebooks/04_feast_feature_store.py`.

**Output cần đạt**

- Pytest biết tìm test trong `tests/`.
- Hai dependency manifest không mâu thuẫn.
- Không còn marker khiến grader nghĩ phần bắt buộc còn dang dở.

---

### Bước 3 — Bootstrap Lite path và sinh toàn bộ dữ liệu

**State hiện tại**

- Chưa có dependency, data hoặc notebook `.ipynb`.

**Cần làm**

- Chạy setup chính thức để chứng minh repo có thể được dựng từ sạch.

**Làm như nào**

```bash
bash setup-lite.sh 2>&1 | tee setup-lite.log
source .venv/bin/activate
```

Sau đó xác minh:

```bash
wc -l data/corpus_vn.jsonl data/golden_set.jsonl data/agent_queries.jsonl
ls notebooks/[0-9]*.ipynb
```

Giá trị cần thấy: corpus 1000 dòng, golden set 50 dòng, có 8 notebook `.ipynb`.

**Làm ở đâu**

- Root repo trong WSL.

**Output cần đạt**

- Setup kết thúc bằng `All checks passed`.
- Có `.venv`, `.env` local, data core/advanced và 8 `.ipynb`.
- Không commit `setup-lite.log` nếu log có thông tin máy không cần thiết; nếu
  muốn lưu log chấm bài, chuyển bản đã kiểm tra vào `submission/logs/`.

---

### Bước 4 — Khóa baseline bằng test, verify và benchmark

**State hiện tại**

- Logic có vẻ đầy đủ qua static review nhưng chưa được chạy trên máy này.

**Cần làm**

- Chạy ba gate trước notebook: unit test, smoke test, quality/latency benchmark.

**Làm như nào**

```bash
make test
make verify-lite
make benchmark | tee benchmark-final.txt
```

Kiểm tra pytest thực sự collect test từ `tests/`; không chấp nhận trạng thái
`no tests ran`. README hiện ghi 34 test nhưng repo thực có nhiều hơn; tiêu chí
là tất cả test được collect đều pass.

**Làm ở đâu**

- Root repo.

**Output cần đạt**

- `make test` exit code 0, không skip bất thường và không phải `no tests ran`.
- `make verify-lite` in `All checks passed`.
- Benchmark in `PASS — hybrid beats keyword ... semantic ...`.
- Lưu số avg Precision@10 và slice để dùng đúng số thật trong reflection.

**Nếu fail**

- RRF: kiểm tra đúng `1/(60 + rank)`, `rank` bắt đầu từ 1, pull depth 50.
- Model download: chạy lại khi mạng ổn; không commit model cache.
- Không thay golden set/corpus để làm đẹp metric.

---

### Bước 5 — NB1: Embeddings và vector indexing (20 điểm)

**State hiện tại**

- Loop batch=64, payload và assertion 1000 đã có; chưa có output.

**Cần làm**

- Chạy NB1 từ đầu đến cuối và xác minh cả query literal lẫn paraphrase.

**Làm như nào**

1. Embed `title + ' ' + text` theo batch 64.
2. Upsert đúng collection `lab19`.
3. Giữ assertion `client.count(...).count == 1000`.
4. Đếm topic trong top-5 paraphrase; mục tiêu ít nhất 3/5 là `cloud`, tốt nhất
   5/5.

Chạy riêng:

```bash
jupyter nbconvert --to notebook --execute --inplace \
  notebooks/01_embeddings_index.ipynb --ExecutePreprocessor.timeout=900
```

**Làm ở đâu**

- Source: `notebooks/01_embeddings_index.py`.
- Deliverable: `notebooks/01_embeddings_index.ipynb`.

**Output cần đạt**

- Dòng `Indexed: 1000 vectors`.
- Top-5 của query `cloud computing và tự động mở rộng` hiện rõ title, topic,
  score.
- Top-5 của query không chứa literal `cloud` bị chi phối bởi topic `cloud`.
- Ảnh `submission/screenshots/01_nb1_index_top5_paraphrase.png` chứa được cả
  count và kết quả cần chấm; nếu không vừa, dùng hai ảnh rõ ràng.

---

### Bước 6 — NB2: Hybrid BM25 + vector + RRF (25 điểm)

**State hiện tại**

- `search_hybrid()` đã cộng hai ranked list bằng rank 1-based và RRF k=60;
  chưa có bảng thực đo.

**Cần làm**

- Giữ đúng formula và chạy đủ 50 golden queries.
- Chứng minh hybrid thắng nghiêm ngặt trên trung bình và có bảng slice.

**Làm như nào**

```bash
jupyter nbconvert --to notebook --execute --inplace \
  notebooks/02_hybrid_search_rrf.ipynb --ExecutePreprocessor.timeout=900
```

Review code trước khi chạy:

```python
for rank, doc_id in enumerate(ids, start=1):
    score[doc_id] += 1.0 / (rrf_k + rank)
```

Không dùng raw cosine/BM25 score để cộng trực tiếp vì hai thang điểm khác nhau.

**Làm ở đâu**

- `notebooks/02_hybrid_search_rrf.py` và `.ipynb` tương ứng.

**Output cần đạt**

- Bảng avg có `hybrid > keyword` **và** `hybrid > semantic`.
- Slice `mixed`: hybrid thắng; `paraphrase`: semantic thắng hoặc gần nhất theo
  wording rubric; `exact`: BM25 thắng hoặc gần nhất.
- Ảnh `02_nb2_precision_and_slices.png` đọc được cả hai bảng.

**Fallback có điều kiện**

- Nếu Lite model không đạt paraphrase sau khi xác nhận code đúng, mới thử backend
  multilingual/bge-m3. Vì NB1/NB2 hiện hard-code `TextEmbedding`, muốn đổi phải
  refactor chúng dùng `app.embeddings.Embedder` và dimension động, sau đó xóa/rebuild
  collection và chạy lại toàn bộ NB1–NB3. Không trộn output của hai model.

---

### Bước 7 — NB3: FastAPI và server-side latency (25 điểm)

**State hiện tại**

- `SearchResponse` có `latency_ms`; route đo bằng `time.perf_counter()` quanh
  search; notebook chưa chạy.

**Cần làm**

- Đảm bảo port 8000 rảnh, warm model/index, benchmark 100 call cho mỗi mode.

**Làm như nào**

```bash
ss -ltnp | grep ':8000' || true
jupyter nbconvert --to notebook --execute --inplace \
  notebooks/03_search_api_benchmark.ipynb --ExecutePreprocessor.timeout=900
```

Notebook phải đọc `body['latency_ms']` cho cột server-side. Không dùng
`P99(wall)` để kết luận rubric. Nếu P99 hybrid >=50 ms, chạy 10–20 warm-up
queries rồi benchmark lại; chỉ tối ưu sau khi profile, không giảm chất lượng/
depth RRF tùy tiện.

**Làm ở đâu**

- API: `app/main.py`, search: `app/search.py`.
- Evidence: `notebooks/03_search_api_benchmark.ipynb`.

**Output cần đạt**

- Một response hợp lệ có query, mode, top_k, `latency_ms`, hits.
- Bảng P50/P95/P99 của keyword, semantic, hybrid.
- Dòng `PASS — hybrid P99 < 50ms` dựa trên server-side latency.
- Process uvicorn được terminate sau notebook.
- Ảnh `03_nb3_api_latency.png` hiển thị response và bảng/PASS.

---

### Bước 8 — NB4: Feast feature store (25 điểm)

**State hiện tại**

- Đã định nghĩa đúng 3 views nhưng chưa có Parquet, registry hoặc materialize.

**Cần làm**

- Chạy NB4 trên Feast state sạch để output `feast apply` thể hiện rõ 3 views
  được tạo, sau đó materialize, online lookup, latency và PIT join.

**Làm như nào**

Trước lần chạy evidence cuối, bảo đảm không có registry cũ. Chỉ xóa đúng các
artifact ignored bên trong `app/feast_repo/`, không xóa source:

```bash
rm -f app/feast_repo/registry.db app/feast_repo/online_store.db
rm -rf app/feast_repo/data
jupyter nbconvert --to notebook --execute --inplace \
  notebooks/04_feast_feature_store.ipynb --ExecutePreprocessor.timeout=900
cd app/feast_repo
feast feature-views list
cd ../..
```

**Làm ở đâu**

- Definitions: `app/feast_repo/feature_views.py`.
- Config: `app/feast_repo/feature_store.yaml`.
- Evidence: `notebooks/04_feast_feature_store.ipynb`.

**Output cần đạt**

- Ba Parquet source được sinh.
- `feast apply` exit 0 và registry/list có đúng:
  `user_profile_features`, `item_popularity_features`,
  `query_velocity_features`.
- Materialize log thể hiện rows được ghi vào online store.
- `get_online_features()` cho `u_001` trả dict có giá trị, không chỉ key rỗng.
- 100-call P99 được in và mục tiêu `<10 ms`.
- PIT result có đúng 3 rows và các feature columns.
- Ảnh `04_nb4_feast_apply_materialize.png` và
  `04_nb4_online_p99_pit.png`.

---

### Bước 9 — NB5: Filtered Search (10 điểm advanced)

**State hiện tại**

- Ground truth brute-force, post-filter và Qdrant filtered-ANN đã implement;
  chưa có output.

**Cần làm**

- Chạy bảng recall theo selectivity và over-fetch ladder.

**Làm như nào**

```bash
jupyter nbconvert --to notebook --execute --inplace \
  notebooks/05_filtered_search.ipynb --ExecutePreprocessor.timeout=900
```

Ground truth phải là exact top-k **trong subset khớp filter**, không phải top-k
toàn corpus.

**Làm ở đâu**

- `app/filters.py`, `app/metadata.py`, NB5.

**Output cần đạt**

- Khi selectivity khoảng 4%, post-filter giảm rõ/tiệm cận 0; filtered-ANN =1.00.
- Ladder cho thấy phải fetch khoảng 500/1000 doc (~50%) mới cứu recall.
- Ảnh `05_nb5_filter_recall_overfetch.png` chứa hai bảng.

---

### Bước 10 — NB6: Agentic Retrieval (12 điểm advanced)

**State hiện tại**

- Planner/tool/reflection/context đã có; `agent_queries.jsonl` và Feast feature
  runtime chưa được kiểm chứng.

**Cần làm**

- Chạy sau NB4 để `build_context()` thực sự có Feast features.
- Giữ ngân sách mọi chiến lược bằng đúng 16 docs.

**Làm như nào**

```bash
test -f data/agent_queries.jsonl || make gen-advanced
jupyter nbconvert --to notebook --execute --inplace \
  notebooks/06_agent_retrieval.ipynb --ExecutePreprocessor.timeout=900
```

Kiểm tra `sum(top_k per call) <= 16`; không cho agent nhiều document hơn
single-shot.

**Làm ở đâu**

- `app/agent.py`, `notebooks/06_agent_retrieval.py`.

**Output cần đạt**

- Bảng 3 strategy cùng budget: agentic no-filter > single-shot cả recall lẫn
  balance.
- Markdown/output giải thích `agentic (+filter)` thấp hơn vì filter topic suy
  đoán loại nhầm document ở cluster lân cận.
- Reflection trace cho thấy retry khi filter quá chặt.
- `build_context()` in `features` có giá trị Feast và `doc_ids` không rỗng.
- Ảnh `06_nb6_agentic_context.png`.

---

### Bước 11 — NB7: Semantic Cache (12 điểm advanced)

**State hiện tại**

- Threshold/TTL/namespace implementation đã có; chưa đo sweep và chưa có leak
  evidence.

**Cần làm**

- Chạy sweep có cả lợi ích và lỗi, chọn threshold dựa trên chính corpus.

**Làm như nào**

```bash
jupyter nbconvert --to notebook --execute --inplace \
  notebooks/07_semantic_cache.ipynb --ExecutePreprocessor.timeout=900
```

Trong phần diễn giải, dùng số thực đo để chọn threshold (dự kiến quanh 0.85),
không copy 0.75 từ AWS như hằng số phổ quát.

**Làm ở đâu**

- `app/cache.py`, NB7.

**Output cần đạt**

- Bảng có hai cột rõ: `tiết kiệm` và `trả lời sai`.
- Giải thích vì sao 0.75 chưa đủ an toàn với corpus này và threshold nào cân
  bằng tốt hơn.
- TTL: trước hạn HIT, sau hạn MISS, stale eviction >=1.
- `namespaced=False`: Globex nhận secret ACME; `True`: MISS.
- Ảnh `07_nb7_threshold_tenant_leak.png`.

---

### Bước 12 — NB8: Feature Engineering (12 điểm advanced)

**State hiện tại**

- Sáu họ feature, leakage experiment, PIT/latest join và ODFV đã có; chưa chạy.

**Cần làm**

- Chạy notebook trên Python/Feast version đã setup và giữ toàn bộ bảng output.

**Làm như nào**

```bash
jupyter nbconvert --to notebook --execute --inplace \
  notebooks/08_feature_engineering.ipynb --ExecutePreprocessor.timeout=900
```

Nếu ODFV serialize lỗi trên Python 3.14, xác nhận setup đã áp dill override;
phương án ổn định hơn là dùng Python 3.12/3.13 từ Bước 1.

**Làm ở đâu**

- `app/features.py`.
- `app/feast_repo_ondemand/definitions.py`.
- NB8.

**Output cần đạt**

- `target-naive` trên `session_id` có gap >0.30.
- `target-in-fold` gap xấp xỉ 0 (và trong tolerance test <0.10).
- In % row leakage, AUC latest, AUC PIT và chênh lệch.
- Cùng `u_000`, hai amount tạo hai `amount_vs_avg` khác nhau.
- Ảnh `08_nb8_leakage_pit_odfv.png`.

---

### Bước 13 — Bonus Challenge (20 điểm)

**State hiện tại**

- Chưa có `bonus/`.

**Cần làm**

Tạo đúng ba deliverable:

1. `bonus/ARCHITECTURE.md` ít nhất 600 từ (nên 800–1000 từ).
2. `bonus/agent.py` có `HybridMemoryAgent.remember()` và `.recall()`.
3. `bonus/demo.py` chạy 5 query và exit 0.

**Làm như nào**

`ARCHITECTURE.md` phải có:

- Mermaid/ASCII diagram nối ingestion → chunk/embed → Qdrant episodic memory;
  batch/stream → Feast stable/recent features; retrieval + feature lookup →
  context assembler → LLM.
- Ba quyết định riêng, mỗi quyết định viết rõ **X vs Y, chọn X vì..., đánh đổi...**:
  chunking, feature schema và freshness.
- Ít nhất một phân tích riêng cho tiếng Việt: code-switching vi/en, dấu/typo,
  tokenizer/embedding multilingual, và có thể privacy theo Nghị định 13.
- Một rejected alternative được gọi tên và có lý do.
- `What this POC doesn't handle yet`.

POC nên chạy offline/Lite, filter Qdrant bằng `user_id`, lấy Feast profile nếu
có và degrade gracefully nếu registry chưa sẵn sàng. Không cần gọi LLM thật.

Chạy gate:

```bash
python bonus/demo.py | tee bonus-demo.txt
python - <<'PY'
from bonus.agent import HybridMemoryAgent
assert hasattr(HybridMemoryAgent, 'remember')
assert hasattr(HybridMemoryAgent, 'recall')
print('bonus API OK')
PY
```

**Làm ở đâu**

- Thư mục mới `bonus/`.

**Output cần đạt**

- Architecture document ≥600 từ và có diagram.
- Đủ 3 explicit tradeoffs, Vietnamese awareness, rejected alternative.
- `demo.py` in đúng 5 query/context và exit 0.
- Ảnh `submission/screenshots/09_bonus_demo.png`.

---

### Bước 14 — Chạy toàn bộ notebook theo đúng cách grader chạy

**State hiện tại**

- Các notebook có thể pass riêng nhưng chưa chứng minh pass tuần tự.

**Cần làm**

- Execute NB1→NB8 từ source hiện tại và giữ output cell.

**Làm như nào**

```bash
make notebooks
```

Sau đó kiểm tra nhanh metadata notebook và lỗi output:

```bash
find notebooks -maxdepth 1 -name '[0-9]*.ipynb' -size +0 -print
grep -R '"output_type": "error"' notebooks/*.ipynb && echo 'FOUND ERROR' || true
git status --short
```

Mở Jupyter để review trực quan, tránh output bị cắt hoặc bảng khó đọc:

```bash
make lab
```

**Làm ở đâu**

- Root repo; output nằm trong 8 file `.ipynb`.

**Output cần đạt**

- `make notebooks` báo PASS cho cả 8 notebook.
- Không notebook nào có error cell.
- Output được preserve và file `.ipynb` được Git track để nộp.

---

### Bước 15 — Hoàn thiện reflection và bộ screenshot

**State hiện tại**

- Reflection trống, folder screenshot chưa tồn tại.

**Cần làm**

- Điền reflection bằng số đo thật, tối đa 200 từ cho phần câu hỏi.
- Chụp bằng chứng rõ, không chỉ chụp code.

**Làm như nào**

Reflection phải trả lời:

- Mode nào thắng `exact`, `paraphrase`, `mixed` dựa trên bảng NB2.
- Vì sao: lexical exact signal, semantic paraphrase signal, RRF robustness.
- Khi nào không dùng hybrid: pure BM25 cho exact identifiers/log codes và
  latency/cost tối thiểu; pure vector cho paraphrase đa ngữ khi lexical signal
  kém và model embedding đã được đánh giá.
- Điền tên, cohort, `Path đã chạy: lite`; tick bonus khi đã hoàn thành.

Danh sách ảnh tối thiểu:

```text
submission/screenshots/
  01_nb1_index_top5_paraphrase.png
  02_nb2_precision_and_slices.png
  03_nb3_api_latency.png
  04_nb4_feast_apply_materialize.png
  04_nb4_online_p99_pit.png
  05_nb5_filter_recall_overfetch.png
  06_nb6_agentic_context.png
  07_nb7_threshold_tenant_leak.png
  08_nb8_leakage_pit_odfv.png
  09_bonus_demo.png
```

**Làm ở đâu**

- `submission/REFLECTION.md`.
- `submission/screenshots/`.

**Output cần đạt**

- Reflection không còn placeholder, đúng giới hạn từ và khớp số output.
- Mỗi criterion có thể truy ngược tới ít nhất một output cell và một screenshot
  đọc được.

---

### Bước 16 — Clean-room verification trước khi nộp

**State hiện tại**

- Chạy trong working copy chưa đủ chứng minh người chấm clone mới vẫn chạy.

**Cần làm**

- Clone commit cuối sang thư mục tạm và chạy lại đúng entrypoint rubric.

**Làm như nào**

Trước hết commit tất cả deliverable cần nộp, rồi trong WSL:

```bash
git diff --check
git status --short
tmpdir=$(mktemp -d)
git clone . "$tmpdir/lab19"
cd "$tmpdir/lab19"
bash setup-lite.sh
source .venv/bin/activate
make test
make verify-lite
make benchmark
make notebooks
python bonus/demo.py
```

Không dùng data/model/registry cũ từ working copy. Nếu clean clone fail, sửa ở
repo chính, commit, rồi clone mới lại; không vá riêng clone tạm.

**Làm ở đâu**

- Một thư mục tạm của WSL, tách khỏi working copy.

**Output cần đạt**

- Tất cả lệnh exit 0.
- 8 notebook PASS.
- Benchmark hybrid thắng và latency gates đạt.
- Bonus demo in 5 outputs.

---

### Bước 17 — Review Git và submit public URL

**State hiện tại**

- Remote đã có nhưng chưa có deliverable cuối và chưa xác minh public.

**Cần làm**

- Chỉ push source/deliverable cần chấm, không push secret/runtime DB.

**Làm như nào**

```bash
git status --short
git diff --check
git ls-files | grep -E '(^\.env$|\.venv|registry\.db|online_store\.db)' && echo 'REMOVE RUNTIME FILES' || true
git add pyproject.toml notebooks/*.py notebooks/*.ipynb submission bonus LAB_PLAN_MAX_SCORE.md
git commit -m "Complete Lab 19 core, advanced, and bonus deliverables"
git push -u origin lab19-max-score
```

Merge về `main` trên GitHub hoặc local rồi push `main`. Mở repo ở cửa sổ ẩn
danh/incognito để chắc chắn người không đăng nhập vẫn xem được.

**Làm ở đâu**

- Git/terminal và GitHub.

**Output cần đạt**

- Public GitHub URL mở được không cần đăng nhập.
- Main branch chứa 8 executed notebooks, screenshots, reflection, bonus và
  source đã sửa.
- Repo giữ public đến khi công bố điểm.
- Paste đúng URL repo vào LMS; không cần PR.

## 5. Checklist nghiệm thu cuối cùng

### Core 100

- [ ] NB1: count=1000; top-5 literal; paraphrase top-5 chủ yếu cloud.
- [ ] NB2: RRF k=60/rank 1-based; hybrid thắng hai mode; slice đúng xu hướng.
- [ ] NB3: response đúng schema; bảng 3 mode; hybrid server P99 <50 ms.
- [ ] NB4: 3 views; materialize; online dict; 100-call P99 <10 ms; PIT 3 rows.
- [ ] Clean setup + benchmark chạy lại được.

### Advanced 50

- [ ] NB5: post-filter cliff + filtered-ANN 1.00 + ladder ~50% corpus.
- [ ] NB6: budget=16 công bằng; recall/balance tăng; giải thích filter; context
  có Feast + doc IDs.
- [ ] NB7: saved/wrong columns; threshold có lý; TTL; cross-tenant leak/fix.
- [ ] NB8: naive gap >0.30; in-fold ≈0; PIT/latest leakage; ODFV dynamic.
- [ ] `make test` chạy test thật và pass; `make verify-lite` pass.

### Bonus 20 và submission

- [ ] Architecture ≥600 từ + diagram.
- [ ] 3 explicit tradeoffs + Vietnamese context + rejected alternative.
- [ ] `HybridMemoryAgent.remember()`/`.recall()` chạy.
- [ ] Demo 5 query exit 0.
- [ ] 8 `.ipynb` có output; không error cell.
- [ ] Screenshot đủ và đọc được.
- [ ] Reflection ≤200 từ, dùng số thật.
- [ ] Không commit secret/runtime artifacts.
- [ ] Public URL đã kiểm tra ở incognito và đã nộp LMS.

## 6. Thứ tự ưu tiên nếu thời gian bị giới hạn

1. **Không thỏa hiệp:** Bước 1–8 + 14–17 để khóa core 100.
2. Tiếp theo NB5–NB8; mỗi mission hoàn chỉnh cả output và screenshot trước khi
   sang mission khác.
3. Bonus làm sau khi clean-room core/advanced đã xanh. Bonus không được làm hỏng
   reproducibility của phần chính.

