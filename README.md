# Question-Extractor/PDF Question Parser (LaTeX + Structure)

## Overview
This service extracts structured questions, MCQs, tables, and figures from question-paper PDFs.
Outputs are validated against a candidate-defined JSON Schema.
OCR is performed using docling and structure is reconstructed using GEMINI 2.5 Flash.

## Key Guarantees
- ≤3 min per 10-page PDF
- Up to 5 PDFs processed concurrently (single request)
- Schema-enforced outputs

## API

### POST /ingest
Upload 1 PDF but can handle 5 PDFs concurrently. The API is asynchronous to avoid long waiting times for the users.
There is a 2nd endpoint which is used to poll for results.

### POST /result/{job_id}
The ingest API gives a job_id which can be used to get the results from this endpoint.

## Output
- Hierarchical questions
- MCQs with labeled options
- Tables structured as rows but inside a csv file
- Figures referenced by filename
- Runtime metrics

## Parallelism
Parallelism is achieved via BackgroundTasks in FastAPI.
Semaphore is used to restrict the number of parallel background tasks that can be processed concurrently.

## Running

```
pip install -r requirements.txt
uvicorn main:app --workers 3 --host 0.0.0.0
```

## Notes
[Notes.md](./Notes.md)

## Evaluation
[Eval.md](./eval.md)
