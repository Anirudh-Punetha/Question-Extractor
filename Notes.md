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
- **Backend Optimization:** We use `pypdfium2`, the fastest PDF backend available for Docling.
- **Inference:** Gemini 2.5 Flash is selected for its high token-per-second throughput compared to Pro models.

### Parallelism (≥ 5 Concurrent PDFs)
- **Concurrency Management:** Implemented an `asyncio.Semaphore(5)`. This ensures that even under heavy load, the system processes exactly 5 high-CPU tasks at once, preventing Out-of-Memory (OOM) crashes in a containerized environment.
- **Logging:** All failures are logged to `storage/results/{job_id}_error.log` with full tracebacks.

---

## 3. Structural Correctness
- **Asset Linking:** Diagrams/Figures are extracted as separate PNG files and mapped back to the JSON via stable UUID filenames.
- **Strict JSON:** We use Gemini's `response_schema` to enforce 100% valid JSON output at the token level.

---

## 4. Prioritized Next Steps
1. **Handwriting Support:** Integrate `Tesseract` OCR as a fallback for scanned handwritten papers.
2. **OMR Head:** Add a vision head to detect filled/unfilled MCQ checkboxes.
3. **Caching:** Implement Redis caching for identical PDF hashes to reduce VLM API costs.