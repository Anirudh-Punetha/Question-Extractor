## Baseline
Initial approach flattened all questions and did not enforce schema validity.

## Improvements
1. Introduced candidate-defined JSON Schema
2. Enforced schema at runtime using jsonschema
3. Added hierarchical question representation (Q2 → Q2.a)
4. Structured MCQs and tables
5. Measured and enforced SLA (≤3 minutes)
6. Enabled true parallelism (5 PDFs per request)

## What Worked
- Deterministic structure
- Clear failure modes on schema violations
- GPU-safe parallelism

## Known Limitations
- Figure bounding boxes not extracted
- Heuristic question splitting
- Nougat/VLM accuracy dependent on scan quality
- Structural parsing is heuristic and may miss unconventional exam layouts.

## Next Steps (Priority)
1. Add figure-to-question bbox mapping
2. Confidence scoring for non-MCQ questions
3. Dev-set driven tuning of hierarchy rules