import os, uuid, json, logging, asyncio, re
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field
from pathlib import Path
from pypdf import PdfReader, PdfWriter
import time

# Docling & AI Imports
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
from docling.datamodel.base_models import InputFormat
import google.generativeai as genai

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resilient VLM Pipeline")
genai.configure(api_key="API_KEY_HERE")  # Replace with your actual API key

STORAGE = Path("storage")
ASSETS = STORAGE / "assets"
RESULTS = STORAGE / "results"
for d in [ASSETS, RESULTS]: d.mkdir(parents=True, exist_ok=True)

os.environ['TOKENIZERS_PARALLELISM'] = 'false'
CHUNK_SIZE = 5
GLOBAL_TIMEOUT = 120.0 # 2 minutes per chunk max
MAX_CONCURRENT_PDFS = 5
semaphore = asyncio.Semaphore(MAX_CONCURRENT_PDFS)

# --- Schemas ---
class SubQuestion(BaseModel):
    id: str
    content_latex: str

class QuestionSchema(BaseModel):
    id: str
    type: str
    content_latex: str
    options: Optional[List[str]]
    image_references: List[str]
    table_references: List[str]
    sub_questions: List[SubQuestion]  # Only one level of nesting

class ExtractionBatch(BaseModel):
    questions: List[QuestionSchema]

# --- Helpers ---
def get_converter():
    opts = PdfPipelineOptions()
    opts.do_formula_enrichment = True
    opts.do_table_structure = True
    opts.generate_picture_images = True
    opts.do_ocr = True # Critical for scanned/messy PDFs
    opts.ocr_options = TesseractCliOcrOptions()
    return DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})

# --- Chunk Worker with Timeout ---
async def run_extraction_for_chunk(chunk_path: Path, job_id: str, start_page: int, img_offset: int, tbl_offset: int):
    """Processes a 5-page segment with a hard timeout."""
    try:
        converter = get_converter()
        
        # Application Level Timeout
        result = await asyncio.wait_for(
            asyncio.to_thread(converter.convert, chunk_path),
            timeout=GLOBAL_TIMEOUT
        )
        doc = result.document

        # Asset Mapping
        image_map, table_map = {}, {}
        for i, pic in enumerate(doc.pictures):
            idx = img_offset + i
            fname = f"{job_id}_fig_{idx}.png"
            pic.image.pil_image.save(ASSETS / fname)
            image_map[f"IMAGE_{idx}"] = fname

        for i, tbl in enumerate(doc.tables):
            idx = tbl_offset + i
            fname = f"{job_id}_tbl_{idx}.csv"
            tbl.export_to_dataframe().to_csv(ASSETS / fname, index=False)
            table_map[f"TABLE_{idx}"] = fname

        # Text Transformation
        md_content = doc.export_to_markdown()
        print(md_content)
        print(image_map)
        
        # Regex replacement for Images
        img_pattern = r'<!--\s*image\s*-->'
        for i in range(len(re.findall(img_pattern, md_content, re.IGNORECASE))):
            md_content = re.sub(img_pattern, f"[IMAGE_{img_offset + i}]", md_content, count=1, flags=re.IGNORECASE)

        # VLM Logical Structuring
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = (
                        "Extract ALL questions from this document into JSON format. If there is an image that seems linked to a question, store it in the output."
                        "For any image references you see like [IMAGE_0], [IMAGE_1], etc., "
                        "include the EXACT placeholder (e.g., 'IMAGE_0', 'IMAGE_1') in the image_references array. "
                        "Preserve all LaTeX formatting in content_latex field.\\n\\n"
                        "If you find a table being used in the question, reference it the output using 'TABLE_0', 'TABLE_1', etc. "
                        "Tables do not have placeholders in the markdown, so just note them when they are mentioned.\\n\\n"
                        f"Document content:\\n{md_content}"
                    )
        response = await asyncio.to_thread(model.generate_content, prompt, 
                                          generation_config=genai.GenerationConfig(
                                              response_mime_type="application/json", 
                                              response_schema=ExtractionBatch))
        
        data = ExtractionBatch.model_validate_json(response.text)
        
        # Map filenames back
        processed_qs = []
        for q in data.questions:
            q.image_references = [image_map.get(ref, ref) for ref in q.image_references]
            q.table_references = [table_map.get(ref, ref) for ref in q.table_references]
            processed_qs.append(q.model_dump())
            print(q.image_references)

        return {"status": "success", "questions": processed_qs, "imgs": len(doc.pictures), "tbls": len(doc.tables)}

    except asyncio.TimeoutError:
        logger.error(f"Timeout on pages {start_page}-{start_page+4}")
        return {"status": "failed", "error": "Timeout", "pages": f"{start_page}-{start_page+4}"}
    except Exception as e:
        logger.error(f"Error on pages {start_page}-{start_page+4}: {e}")
        return {"status": "failed", "error": str(e), "pages": f"{start_page}-{start_page+4}"}

# --- Orchestrator ---
async def process_pdf_task(file_path: Path, job_id: str):
    async with semaphore:
        start_time = time.time()
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        
        final_output = {
                        "job_id": job_id,
                        "total_pages": total_pages,
                        "questions": [],
                        "errors": [],
                        "processing_time_sec": 0 # Initialize
                    }
        img_ptr, tbl_ptr = 0, 0

        for i in range(0, total_pages, CHUNK_SIZE):
            writer = PdfWriter()
            chunk_range = reader.pages[i : i + CHUNK_SIZE]
            for page in chunk_range:
                writer.add_page(page)
            
            c_path = STORAGE / f"{job_id}_c{i}.pdf"
            with open(c_path, "wb") as f:
                writer.write(f)
            
            # Execute chunk
            res = await run_extraction_for_chunk(c_path, job_id, i + 1, img_ptr, tbl_ptr)
            
            if res["status"] == "success":
                final_output["questions"].extend(res["questions"])
                img_ptr += res["imgs"]
                tbl_ptr += res["tbls"]
            else:
                final_output["errors"].append({
                    "pages": res["pages"],
                    "reason": res["error"]
                })
            
            if c_path.exists(): os.remove(c_path)

        final_output["processing_time_sec"] = round(time.time() - start_time, 2)

        with open(RESULTS / f"{job_id}.json", "w") as f:
            json.dump(final_output, f, indent=2)

        logger.info(f"Completed Job {job_id}")

# --- Endpoints ---
@app.post("/ingest")
async def ingest(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    jid = str(uuid.uuid4())
    temp = STORAGE / f"{jid}.pdf"
    with open(temp, "wb") as f: f.write(await file.read())
    background_tasks.add_task(process_pdf_task, temp, jid)
    return {"job_id": jid, "status": "queued"}

@app.get("/result/{job_id}")
async def get_result(job_id: str):
    p = RESULTS / f"{job_id}.json"
    return {"status": "completed", "data": json.load(open(p))} if p.exists() else {"status": "processing"}