# Evaluation Plan — PDF Question Parsing System

This document describes how the system will be evaluated for correctness,
performance, and robustness, aligned with the grading rubric.

---

## 1. Evaluation Goals

The evaluation focuses on five dimensions:

1. **Runtime & Parallelism**
2. **Structural Correctness (Schema Compliance)**
3. **Question Extraction Accuracy**
4. **MCQ / Table / Figure Fidelity**
5. **System Stability & Failure Modes**

The system is not evaluated on semantic correctness of answers, only on
structural and representational accuracy.

---

## 2. Test Datasets

### 2.1 Development Set
A fixed set of 5 PDFs provided by the evaluator, containing:
- Mathematical equations
- MCQs with 4–5 options
- Nested questions (e.g., Q1(a), Q1(b))
- Tables
- Embedded figures

These documents are used for qualitative and quantitative checks.

### 2.2 Stress Set
Synthetic PDFs generated to test:
- Maximum page count (10 pages)
- Mixed content density
- Noisy scans (low contrast, skew)

---

## 3. Runtime & Parallelism Evaluation

### 3.1 SLA Measurement

**Metric**
- `total_ms` per PDF (reported in output JSON)

**Procedure**
1. Submit a request with 5 PDFs (each ~10 pages).
2. Record `total_ms` for each PDF.
3. Verify:
   - Each PDF completes in ≤ 180,000 ms
   - All PDFs complete within a single request

**Pass Criteria**
- No SLA violations
- No worker crashes
- Stable GPU utilization

---

### 3.2 Parallelism Verification

**Procedure**
1. Submit a single request with 5 PDFs.
2. Inspect logs and timestamps.
3. Verify:
   - Multiple worker processes active concurrently
   - No serialization of PDFs

**Pass Criteria**
- 5 PDFs processed concurrently using `ProcessPoolExecutor`
- No deadlocks or GPU contention

---

## 4. Structural Correctness Evaluation (Schema)

### 4.1 JSON Schema Validation

**Metric**
- Percentage of outputs passing schema validation

**Procedure**
- All outputs are validated at runtime using `jsonschema`
- Any schema violation results in a hard failure

**Pass Criteria**
- 100% schema compliance
- No missing required fields
- Correct data types for all fields

---

### 4.2 Hierarchical Question Structure

**Checks**
- Parent–child relationships preserved
- Multipart questions nested correctly

**Examples**
- `Q2 → Q2.a → Q2.b`
- Sections represented implicitly via hierarchy

**Pass Criteria**
- No flattened multipart questions
- Child questions never appear at root level incorrectly

---

## 5. Question Extraction Accuracy

### 5.1 Question Recall

**Metric**
- % of visually identifiable questions extracted

**Procedure**
1. Manually count questions in the PDF.
2. Compare with extracted `questions[]`.

**Pass Criteria**
- ≥ 90% question recall on dev set

---

### 5.2 Equation Fidelity

**Checks**
- Mathematical expressions preserved in LaTeX
- No major symbol loss (∫, Σ, superscripts)

**Pass Criteria**
- Visual equivalence between PDF and LaTeX

---

## 6. MCQ Evaluation

### 6.1 MCQ Detection Accuracy

**Checks**
- MCQs correctly classified as `type: mcq`
- Options detected as structured list

**Pass Criteria**
- ≥ 95% MCQs detected
- No MCQs misclassified as descriptive

---

### 6.2 Option Structure

**Checks**
- Each option has:
  - Label (A, B, C, …)
  - LaTeX content
  - Confidence score

**Pass Criteria**
- All options structured
- No options embedded as raw text blobs

---

## 7. Table Evaluation

### 7.1 Structural Table Fidelity

**Checks**
- Tables represented as row/column arrays
- No table rendered as plain text

**Pass Criteria**
- All tables appear in `tables[]`
- Row structure preserved (even if cell content is partial)

---

## 8. Figure Evaluation

### 8.1 Figure Referencing

**Checks**
- Figures exported as image files
- Referenced by filename in output JSON
- Page association present

**Pass Criteria**
- Every figure referenced by filename
- No missing or duplicated references

---

## 9. Robustness & Failure Modes

### 9.1 OCR Failure Handling

**Procedure**
- Corrupt or low-quality PDFs
- Empty pages

**Checks**
- Graceful failure with error messages
- No partial or malformed JSON

---

### 9.2 Schema Failure Handling

**Checks**
- Schema violations raise explicit errors
- Invalid outputs are never returned

---

## 10. Reproducibility

### 10.1 Determinism

**Checks**
- Same PDF → same JSON output
- No non-deterministic ordering

**Pass Criteria**
- Stable outputs across runs

---

## 11. Reporting

### 11.1 Metrics Captured

Each output includes:
- `total_ms`
- PDF identifier
- Structured content

### 11.2 Manual Review Checklist

For each dev PDF:
- ✔ All questions present
- ✔ MCQs structured
- ✔ Tables structured
- ✔ Figures linked
- ✔ Schema valid

---

## 12. Known Limitations (Acknowledged)

- Heuristic question segmentation
- No figure bounding boxes
- Table cell content may be incomplete

These are documented and considered acceptable trade-offs for performance
and robustness.

---

## 13. Summary

This evaluation plan ensures:
- Objective measurement of key constraints
- Transparent correctness criteria
- Reproducible and rubric-aligned assessment

The system is evaluated as a **document understanding pipeline**, not a
semantic reasoning engine.
