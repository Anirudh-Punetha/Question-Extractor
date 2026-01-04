# Question-Extractor/PDF Question Parser (LaTeX + Structure)

## Overview
This service extracts structured questions, MCQs, tables, and figures from question-paper PDFs.
Outputs are validated against a candidate-defined JSON Schema.
OCR is performed using facebook/nougat-base via HuggingFace Transformers.

## Key Guarantees
- ≤3 min per 10-page PDF
- Up to 5 PDFs processed concurrently (single request)
- Schema-enforced outputs
- GPU-safe (single Gunicorn worker)

## API

### POST /parse
Upload up to 5 PDFs.

## Output
- Hierarchical questions
- MCQs with labeled options
- Tables structured as rows
- Figures referenced by filename
- Runtime metrics

## Parallelism
Parallelism is achieved via `ProcessPoolExecutor` inside a single request.
Gunicorn workers are intentionally limited to 1 to avoid GPU contention.

## Running
docker build -t qp .
docker run --gpus all -p 8000:8000 qp
