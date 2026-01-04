import re
import uuid

QUESTION_RE = re.compile(r"\\question\s*(.*)")
MCQ_RE = re.compile(r"\\begin\{choices\}(.*?)\\end\{choices\}", re.S)

def extract_questions(latex: str):
    questions = []
    blocks = latex.split("\\question")

    for i, block in enumerate(blocks[1:], start=1):
        qid = f"Q{i}"
        text = block.strip()

        mcq = MCQ_RE.search(text)
        if mcq:
            options = []
            for j, opt in enumerate(mcq.group(1).split("\\choice")):
                opt = opt.strip()
                if not opt:
                    continue
                options.append({
                    "label": chr(65 + j),
                    "latex": opt,
                    "confidence": 0.9
                })

            questions.append({
                "id": qid,
                "type": "mcq",
                "latex": text,
                "options": options,
                "children": []
            })
        else:
            questions.append({
                "id": qid,
                "type": "descriptive",
                "latex": text,
                "children": []
            })

    return questions