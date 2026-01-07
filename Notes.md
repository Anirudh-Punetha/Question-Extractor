# Implementation Notes: VLM Question Extraction Pipeline

## 1. Technical Approach
We utilize a **Hybrid Extraction Strategy** to ensure high structural fidelity while maintaining the speed required for time-sensitive grading.

- **Baseline:** Traditional OCR + Heuristic Layout Analysis.
- **Improvement:** **Docling (IBM Research)** for native structural parsing + **Gemini 2.5 Flash** for semantic JSON shaping.

### Why this approach?
1. **Formula Fidelity:** Docling's `Formula Enrichment` extracts LaTeX locally, preventing LLM math hallucinations.
2. **Table Reconstruction:** Tables are converted to Markdown via `TableFormer`, allowing the LLM to process data in its most natural textual format.
3. **Sequential Logic:** Docling maintains the logical reading order, which is critical for multi-column exam papers.

---

## 2. Key Constraints Compliance

### Runtime (≤ 3 min / 10 pages)
- **Backend Optimization:** We use Tesseract as the OCR engine in Docling and process the pdf in chunks to keep the execution time low.
- **Inference:** Gemini 2.5 Flash is selected for its high token-per-second throughput compared to Pro models.

### Parallelism (≥ 5 Concurrent PDFs)
- **Concurrency Management:** Implemented an `asyncio.Semaphore(5)`. This ensures that even under heavy load, the system processes exactly 5 high-CPU tasks at once, preventing Out-of-Memory (OOM) crashes in a containerized environment.
- **Logging:** All resuts including failures are stored to `storage/results/{job_id}.json`.

---

## 3. Structural Correctness
- **Asset Linking:** Diagrams/Figures are extracted as separate PNG files and mapped back to the JSON via stable UUID filenames. They are stored in storage/assets/{job_id}_{img_id}.png
- **Strict JSON:** We use Gemini's `response_schema` to enforce 100% valid JSON output at the token level.

---

## 4. What worked well
1. All questions and subquestions are mostly correct.
2. Latex is extracted correctly.
3. Schema adherance is working well.
4. Figures and tables are being extracted.
5. OCR is also working for scanned parts of pages except where the resolution is too low.

--- 

## 5. Problems Identified
1. Figures are often tagged to the question above or below the actual question.
2. False positives for tables where questions are in a column based paper style.

---

## 6. Prioritized Next Steps
1. **Figure Mismatch:** We can try to train a layout parser model like LayoutLM to identify bounding boxes for questions and then process it one bounding box at a time. This will lead to figures and tables being always tagged to the correct question.
2. **Intersecting Questions:** Chunking may lead to a question which is spread across multiple pages to be treated as 2 different questions. We could pass the last question of a chunk and the first question of the next chunk to see if they can be merged together. This can be done with another LLM call.
3. **Caching:** Implement Redis caching for identical PDF hashes to reduce VLM API costs.
4. **Readability:** Since I had to frequently move files between mac and windows as I don't have a personal unix system, I chose to keep everything in 1 file. I have added section headers in the main.py file to indicate where the file can be split and a separate module can be created. Examples of this are `# --- Configuration ---`, `# --- Schemas ---`, `# --- Helpers ---` and `# --- Endpoints ---`.