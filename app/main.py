from fastapi import FastAPI, UploadFile, File, HTTPException
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import tempfile, shutil

from app.worker import process_pdf
from app.config import MAX_WORKERS

app = FastAPI()
executor = ProcessPoolExecutor(max_workers=MAX_WORKERS)

@app.post("/parse")
def parse(files: list[UploadFile] = File(...)):
    if len(files) > MAX_WORKERS:
        raise HTTPException(400, "Max 5 PDFs per request")

    tmp = Path(tempfile.mkdtemp())
    futures = []

    try:
        for f in files:
            pdf_path = tmp / f.filename
            with open(pdf_path, "wb") as out:
                shutil.copyfileobj(f.file, out)

            futures.append(executor.submit(process_pdf, str(pdf_path)))

        results = []
        for fut in as_completed(futures):
            results.append(fut.result())

        return {
            "num_pdfs": len(results),
            "results": results
        }

    finally:
        shutil.rmtree(tmp, ignore_errors=True)