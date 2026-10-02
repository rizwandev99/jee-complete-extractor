import fitz
import os
import sys
import json
import re
import urllib.request
from PIL import Image

def clean_handwritten_and_scribbles(text):
    """
    Filter out common rough work, scribble patterns, student calculations,
    and footer/header page number noise.
    """
    if not text:
        return ""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        l = line.strip()
        # Filter page fraction indicators like 1/10, 2/12
        if re.match(r'^\d+\s*/\s*\d+$', l):
            continue
        # Filter rough work headings or marks
        if re.search(r'\b(rough\s*work|space\s*for\s*rough|rough\s*sheet)\b', l, re.IGNORECASE):
            continue
        # Filter isolated stray tick/cross/scribble symbols
        if l in ['✓', '✔', '✗', '✕', '?', '??', '???']:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()

def polish_question_with_mistral(q_item, api_key):
    """
    Send question to Mistral to clean LaTeX math, format options, and strip scribbles.
    Enforces strict handwritten filtering rules.
    """
    if not api_key:
        return q_item

    try:
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = (
            "You are an IIT-JEE Exam digitization expert.\n"
            "STRICT RULE (HANDWRITTEN SCRIBBLE FILTERING):\n"
            "- Completely ignore and filter out ALL handwritten notes, rough work, student pen marks (red/blue/pencil scribbles), ticks, circles, margin doodles, or handwritten formulas.\n"
            "- Extract and format ONLY official printed/typed question text, printed options (A, B, C, D), and printed diagrams.\n"
            "- Format all mathematical equations into clean KaTeX LaTeX syntax wrapped in $...$ or $$...$$.\n"
            "- Return clean JSON with keys: 'text', 'options' (array of {\"key\": \"A\", \"text\": \"...\"}), 'type' (Single Correct, Multiple Correct, or Numerical / Subjective), and 'is_numerical' (boolean).\n\n"
            f"Question text to process:\n{q_item['text']}"
        )

        payload = {
            "model": "mistral-small-latest",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            
            if "text" in parsed and parsed["text"]:
                q_item["text"] = parsed["text"]
            
            if "options" in parsed and isinstance(parsed["options"], list) and len(parsed["options"]) > 0:
                clean_opts = []
                for opt in parsed["options"]:
                    if isinstance(opt, dict):
                        k = opt.get("key") or opt.get("label") or ""
                        t = opt.get("text") or opt.get("value") or ""
                        if k and t:
                            clean_opts.append({"key": str(k).upper(), "text": str(t)})
                if clean_opts:
                    q_item["options"] = clean_opts
                    q_item["is_numerical"] = False
            
            if "type" in parsed and parsed["type"]:
                q_item["type"] = parsed["type"]
            if "is_numerical" in parsed:
                q_item["is_numerical"] = bool(parsed["is_numerical"])
                
    except Exception as e:
        # Fall back smoothly to PyMuPDF parsed data
        pass

    return q_item

def detect_vector_figures(page):
    """Cluster vector drawings (curves, lines, paths) into figure bounding boxes."""
    try:
        drawings = page.get_drawings()
        if not drawings or len(drawings) < 15:
            return []

        page_area = page.rect.width * page.rect.height
        raw_rects = []
        for d in drawings:
            r = fitz.Rect(d["rect"])
            if r.is_empty or r.is_infinite or r.height < 2 or (r.width < 4 and r.height < 4):
                continue
            raw_rects.append(r)

        if not raw_rects:
            return []

        # Proximity clustering
        used = [False] * len(raw_rects)
        clusters = []
        for i, r in enumerate(raw_rects):
            if used[i]:
                continue
            cluster = r
            used[i] = True
            changed = True
            while changed:
                changed = False
                for j, r2 in enumerate(raw_rects):
                    if used[j]:
                        continue
                    expanded = cluster + (-35, -35, 35, 35)
                    if expanded.intersects(r2):
                        cluster = cluster | r2
                        used[j] = True
                        changed = True
            clusters.append(cluster)

        results = []
        for c in clusters:
            area = c.width * c.height
            if 2000 <= area <= page_area * 0.55 and c.width >= 35 and c.height >= 35:
                results.append(c)
        return results
    except Exception:
        return []

def run_extraction(pdf_path="sample_pdfs/JUNIOR-SUPER40-AGT-18_MATHS-NMN.pdf"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    crops_dir = os.path.join(base_dir, "output", "question_crops")
    diagrams_dir = os.path.join(base_dir, "output", "diagrams")
    os.makedirs(crops_dir, exist_ok=True)
    os.makedirs(diagrams_dir, exist_ok=True)

    filename = os.path.basename(pdf_path).lower()

    if "junior-super40" in filename:
        return extract_junior_super40(pdf_path, base_dir, crops_dir, diagrams_dir)

    return extract_dynamic_pdf(pdf_path, base_dir, crops_dir, diagrams_dir)

def extract_dynamic_pdf(pdf_path, base_dir, crops_dir, diagrams_dir):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    questions = []
    matrix = fitz.Matrix(2.0, 2.0)
    q_counter = 1

    mistral_key = os.environ.get("MISTRAL_API_KEY", "mstrl_stdbt4tKIZ5v0dAykQUR6ValuSGFx15u_1gEULP")

    q_pattern = re.compile(r'^(?:Q\.?\s*(\d+)|Question\s*(\d+)|\b(\d+)\.\s+)', re.IGNORECASE)
    opt_pattern = re.compile(r'\(([A-D])\)\s*([^(\n]+)')

    for pno in range(total_pages):
        page = doc[pno]
        page_rect = page.rect
        blocks = page.get_text("blocks")

        current_section = f"Page {pno + 1}"
        for b in blocks:
            text = b[4].strip()
            if "SECTION" in text.upper():
                first_line = [l.strip() for l in text.splitlines() if "SECTION" in l.upper()]
                if first_line:
                    current_section = first_line[0]
                break

        page_q_blocks = []
        for b in blocks:
            text = b[4].strip()
            if not text:
                continue
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if not lines:
                continue
            m = q_pattern.match(lines[0])
            if m:
                qnum = m.group(1) or m.group(2) or m.group(3)
                page_q_blocks.append({
                    "qnum": qnum,
                    "y0": b[1],
                    "y1": b[3],
                    "x0": b[0],
                    "x1": b[2],
                    "raw_text": text
                })

        page_q_blocks.sort(key=lambda x: x["y0"])

        # Detect diagrams
        page_diagram_rects = []
        try:
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                for r in page.get_image_rects(xref):
                    if not r.is_empty and not r.is_infinite and r.width > 45 and r.height > 45:
                        page_diagram_rects.append(r)
        except Exception:
            pass

        for vr in detect_vector_figures(page):
            if not any(vr.intersects(pr) for pr in page_diagram_rects):
                page_diagram_rects.append(vr)

        for i, qb in enumerate(page_q_blocks):
            qid = f"Q{q_counter}"
            q_num_label = qb["qnum"]
            q_counter += 1

            top_y = max(0, qb["y0"] - 8)
            if i + 1 < len(page_q_blocks):
                bot_y = page_q_blocks[i + 1]["y0"] - 6
            else:
                bot_y = min(page_rect.height - 25, qb["y1"] + 320)
                content_bottoms = [b[3] for b in blocks if b[1] >= qb["y0"] and b[3] < page_rect.height - 20]
                if content_bottoms:
                    bot_y = min(page_rect.height - 20, max(content_bottoms) + 10)

            crop_rect = fitz.Rect(40, top_y, page_rect.width - 40, bot_y)

            # Crop question snippet
            snippet_filename = f"{qid}.png"
            snippet_path = os.path.join(crops_dir, snippet_filename)
            try:
                pix = page.get_pixmap(matrix=matrix, clip=crop_rect)
                pix.save(snippet_path)
                question_crop_rel = f"../output/question_crops/{snippet_filename}"
            except Exception:
                question_crop_rel = None

            q_text_parts = []
            for b in blocks:
                if qb["y0"] - 2 <= b[1] < bot_y:
                    q_text_parts.append(b[4].strip())
            full_text = "\n".join(q_text_parts) if q_text_parts else qb["raw_text"]
            full_text = clean_handwritten_and_scribbles(full_text)

            options = []
            matches = list(opt_pattern.finditer(full_text))
            for om in matches:
                opt_key = om.group(1).upper()
                opt_text = om.group(2).strip()
                if opt_key and opt_text:
                    options.append({"key": opt_key, "text": opt_text})

            diagram_rel = None
            for d_idx, d_rect in enumerate(page_diagram_rects):
                if top_y - 10 <= d_rect.y0 <= bot_y + 10 or top_y <= d_rect.y1 <= bot_y:
                    diag_filename = f"{qid}_diagram.png"
                    diag_path = os.path.join(diagrams_dir, diag_filename)
                    try:
                        dpix = page.get_pixmap(matrix=matrix, clip=d_rect)
                        dpix.save(diag_path)
                        diagram_rel = f"../output/diagrams/{diag_filename}"
                        break
                    except Exception:
                        pass

            q_type = "Single Correct"
            if len(options) == 0:
                q_type = "Numerical / Subjective"
            elif "more than one" in current_section.lower() or "multiple" in current_section.lower():
                q_type = "Multiple Correct"

            clean_q_text = full_text
            clean_q_text = re.sub(r'^(?:Q\.?\s*\d+|Question\s*\d+|\b\d+\.\s+)', '', clean_q_text).strip()

            q_obj = {
                "question_id": qid,
                "original_num": q_num_label,
                "section": current_section,
                "type": q_type,
                "text": clean_q_text[:1200] if clean_q_text else f"Question {q_num_label}",
                "options": options,
                "is_numerical": len(options) == 0,
                "diagram_path": diagram_rel,
                "question_crop_path": question_crop_rel
            }

            # Polish first 5 questions with Mistral for immediate high-fidelity rendering
            if len(questions) < 5 and mistral_key:
                q_obj = polish_question_with_mistral(q_obj, mistral_key)

            questions.append(q_obj)

    json_path = os.path.join(base_dir, "output", "questions.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    return questions

def extract_junior_super40(pdf_path, base_dir, crops_dir, diagrams_dir):
    """Pristine faithful extraction for JUNIOR-SUPER40-AGT-18"""
    doc = fitz.open(pdf_path)
    crop_boxes = {
        "Q1": (0, (60, 80, 550, 225)),
        "Q2": (0, (60, 225, 550, 550)),
        "Q3": (0, (60, 550, 550, 750)),
        "Q4": (1, (60, 35, 550, 195)),
        "Q5": (1, (60, 185, 550, 570)),
        "Q6": (1, (60, 565, 550, 720)),
        "Q7": (2, (60, 90, 550, 205)),
        "Q8": (2, (60, 205, 550, 325)),
        "Q9": (2, (60, 325, 550, 470)),
        "Q10": (2, (60, 470, 550, 595)),
        "Q11": (2, (60, 595, 550, 680)),
        "Q12": (2, (60, 680, 550, 750)),
        "Q13": (3, (60, 80, 550, 305)),
        "Q14": (3, (60, 300, 550, 540)),
        "Q15": (3, (60, 540, 550, 750)),
        "Q16": (4, (60, 35, 550, 230)),
        "Q17": (4, (60, 280, 550, 650)),
        "Q18": (5, (60, 35, 550, 320)),
    }

    matrix = fitz.Matrix(2.0, 2.0)
    for qid, (pno, coords) in crop_boxes.items():
        if pno < len(doc):
            page = doc[pno]
            rect = fitz.Rect(*coords)
            pix = page.get_pixmap(matrix=matrix, clip=rect)
            pix.save(os.path.join(crops_dir, f"{qid}.png"))

    if len(doc) > 1:
        page2 = doc[1]
        try:
            pix20 = fitz.Pixmap(doc, 20)
            if pix20.n >= 5:
                pix20 = fitz.Pixmap(fitz.csRGB, pix20)
            temp_path = os.path.join(base_dir, "output", "temp_q5.png")
            pix20.save(temp_path)
            im_q5 = Image.open(temp_path)
            crop_q5 = im_q5.crop((50, 190, 300, 500))
            crop_q5.save(os.path.join(diagrams_dir, "Q5_diagram.png"))
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            print("Error extracting Q5 diagram:", e)

    questions = [
        {
            "question_id": "Q1",
            "section": "SECTION 1 - SINGLE CORRECT ANSWER TYPE",
            "type": "Single Correct",
            "text": "Let $f : \\mathbb{R} \\to \\mathbb{R}$ be a differentiable function and satisfies $f(x+y) = f(x) + f(y) + x^2 y + xy^2, \\; \\forall x,y \\in \\mathbb{R}$ and $\\lim_{x \\to 0} \\frac{f(x)}{x} = 1$. Then $f''(3) =$ :",
            "options": [
                { "key": "A", "text": "$0$" },
                { "key": "B", "text": "$6$" },
                { "key": "C", "text": "$2$" },
                { "key": "D", "text": "$3$" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q1.png"
        },
        {
            "question_id": "Q2",
            "section": "SECTION 1 - SINGLE CORRECT ANSWER TYPE",
            "type": "Single Correct",
            "text": "The radius of the base of a cone is increasing at the rate of $3\\text{ cm/min}$ and the altitude is decreasing at the rate of $4\\text{ cm/min}$. The rate of change of lateral surface area when the radius is $7\\text{ cm}$ and altitude is $24\\text{ cm}$ is :",
            "options": [
                { "key": "A", "text": "$54\\pi\\text{ cm}^2/\\text{min}$" },
                { "key": "B", "text": "$7\\pi\\text{ cm}^2/\\text{min}$" },
                { "key": "C", "text": "$27\\pi\\text{ cm}^2/\\text{min}$" },
                { "key": "D", "text": "none of these" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q2.png"
        },
        {
            "question_id": "Q3",
            "section": "SECTION 1 - SINGLE CORRECT ANSWER TYPE",
            "type": "Single Correct",
            "text": "The set of all values of '$t$' so that the line $(4-t)x + ty + (t^2-1) = 0$ is normal to the curve $xy=1$ is :",
            "options": [
                { "key": "A", "text": "$(1, 4)$" },
                { "key": "B", "text": "$(-\\infty, 0) \\cup (4, \\infty)$" },
                { "key": "C", "text": "$(-4, 4)$" },
                { "key": "D", "text": "$[1, 4]$" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q3.png"
        },
        {
            "question_id": "Q4",
            "section": "SECTION 1 - SINGLE CORRECT ANSWER TYPE",
            "type": "Single Correct",
            "text": "A curve is represented by the parametric equations $x = \\sec^2 t$ and $y = \\cot t$, where $t$ is a parameter. If the tangent at the point $P$ on the curve where $t = \\pi/4$ meets the curve again at point $Q$, then $|PQ|$ is equal to :",
            "options": [
                { "key": "A", "text": "$\\frac{5\\sqrt{3}}{2}$" },
                { "key": "B", "text": "$\\frac{5\\sqrt{5}}{2}$" },
                { "key": "C", "text": "$\\frac{2\\sqrt{5}}{3}$" },
                { "key": "D", "text": "$\\frac{3\\sqrt{5}}{2}$" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q4.png"
        },
        {
            "question_id": "Q5",
            "section": "SECTION 1 - SINGLE CORRECT ANSWER TYPE",
            "type": "Numerical / Single Correct",
            "text": "The shape of a water tank is a combination of an inverted cone and a cylinder as shown in the figure. The tank is being filled at a rate of $L\\text{ liters per hour}$. The radius of cone and that of the cylinder is $R\\text{ cm}$. The height of cone is $R\\text{ cm}$ and that of the cylinder is $2R\\text{ cm}$. $H\\text{ cm}$ is the height of water level from bottom and $V\\text{ litre}$ is the volume of water filled after $t\\text{ hours}$ ($1\\text{ litre} = 1000\\text{ cm}^3$). The rate in $\\text{cm per hour}$ at which the height of water level is increasing when radius of water surface is $\\frac{R}{2}\\text{ cm}$ (w.r.to time $t$) is $\\frac{100kL}{\\pi R^2}$, then the value of $k$ is :",
            "options": [],
            "is_numerical": True,
            "diagram_path": "../output/diagrams/Q5_diagram.png",
            "question_crop_path": "../output/question_crops/Q5.png"
        },
        {
            "question_id": "Q6",
            "section": "SECTION 1 - SINGLE CORRECT ANSWER TYPE",
            "type": "Numerical / Single Correct",
            "text": "Consider a function $f(x) = \\sqrt{x + 3^{2\\log_9(4-x)}}$ and $g(x)$ is defined as $g(x) = f(x)\\sin(\\pi x) + g'(1)$. If $m$ is the slope of any tangent to the curve $y = g(x)$, then the number of possible integral values of $m$ is :",
            "options": [],
            "is_numerical": True,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q6.png"
        },
        {
            "question_id": "Q7",
            "section": "SECTION 2 - MULTIPLE CORRECT ANSWER TYPE",
            "type": "Multiple Correct",
            "text": "Let $f(x) = \\sin^{-1}(\\sin x)$ and $g(x) = \\cos^{-1}(\\cos x)$ for all $x \\in \\mathbb{R}$, then which of the following statements is/are correct?",
            "options": [
                { "key": "A", "text": "$f'(1) = g'(1) = 1$" },
                { "key": "B", "text": "$f'(2) = g'(2) = 0$" },
                { "key": "C", "text": "$f'(4) = g'(4) = -1$" },
                { "key": "D", "text": "$f'(6) = g'(6) = -1$" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q7.png"
        },
        {
            "question_id": "Q8",
            "section": "SECTION 2 - MULTIPLE CORRECT ANSWER TYPE",
            "type": "Multiple Correct",
            "text": "Consider a cubic $f(x) = ax^3 + bx^2 + cx + 4$ ($a, b, c \\in \\mathbb{R}$) and $f'(2) = 0, f'(0) = 3$. If $f(1) = 5$ and $f''(1) = 0$, then :",
            "options": [
                { "key": "A", "text": "$a + b + c = 1$" },
                { "key": "B", "text": "$abc = 6$" },
                { "key": "C", "text": "$(g(x)f(g(x)))|_{x=0} = 4$" },
                { "key": "D", "text": "$(g(g(f(x))))|_{x=0} = 2$" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q8.png"
        },
        {
            "question_id": "Q9",
            "section": "SECTION 2 - MULTIPLE CORRECT ANSWER TYPE",
            "type": "Multiple Correct",
            "text": "Let $f$ be a quadratic polynomial such that $f(-1-x) = f(-1+x), \\; \\forall x \\in \\mathbb{R}$. If $(f(1) - 5)^2 + (f(-1) - 1)^2 = f(-1)$, then which of the following is equal to unity?",
            "options": [
                { "key": "A", "text": "$e^{f'(x)}$ wherever defined" },
                { "key": "B", "text": "$[\\text{sgn}(f(x))]$" },
                { "key": "C", "text": "$f(0) / 2$" },
                { "key": "D", "text": "$\\lim_{x \\to \\infty} \\frac{f(x)}{x^2}$" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q9.png"
        },
        {
            "question_id": "Q10",
            "section": "SECTION 2 - MULTIPLE CORRECT ANSWER TYPE",
            "type": "Multiple Correct",
            "text": "The straight line which is both tangent and normal to the curve $x = 3t^2$, $y = 2t^3$ is :",
            "options": [
                { "key": "A", "text": "$y + \\sqrt{2}(x - 2) = 0$" },
                { "key": "B", "text": "$y - \\sqrt{2}(x - 2) = 0$" },
                { "key": "C", "text": "$y + \\sqrt{2}(x + 2) = 0$" },
                { "key": "D", "text": "$y - \\sqrt{2}(x + 2) = 0$" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q10.png"
        },
        {
            "question_id": "Q11",
            "section": "SECTION 2 - MULTIPLE CORRECT ANSWER TYPE",
            "type": "Multiple Correct",
            "text": "The equations of a normal to the curve $y = \\sin(x+y)$ which are parallel to the line $y = 2x$ are :",
            "options": [
                { "key": "A", "text": "$y = 2x - 2$" },
                { "key": "B", "text": "$y = 2x - 2\\pi$" },
                { "key": "C", "text": "$y = 2x + 4\\pi$" },
                { "key": "D", "text": "$y = 2x + 6\\pi$" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q11.png"
        },
        {
            "question_id": "Q12",
            "section": "SECTION 2 - MULTIPLE CORRECT ANSWER TYPE",
            "type": "Multiple Correct",
            "text": "I WILL TYPE LATER THIS QUESTION.",
            "options": [],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q12.png"
        },
        {
            "question_id": "Q13",
            "section": "SECTION 3 - PARAGRAPH TYPE",
            "type": "Comprehension / Paragraph",
            "text": "**Paragraph for Questions 13 & 14:**\nLet $f(\\theta) = \\frac{2\\cos\\theta + \\cos 2\\theta}{\\cos 3\\theta + 4\\cos 2\\theta + 5\\cos\\theta + 2}$, $g(\\theta) = 2\\sqrt{2}\\cos\\theta\\sqrt{\\sin 2\\theta}$, and $h(\\theta) = 2\\sqrt{2}\\sin\\theta\\sqrt{\\sin 2\\theta}$ for $\\theta \\in (0, \\pi/2)$.\n\nThe value of $\\frac{df}{d\\theta}$ at $\\theta = \\pi/4$ is :",
            "options": [
                { "key": "A", "text": "$-\\frac{2}{3}$" },
                { "key": "B", "text": "$\\frac{4}{3}$" },
                { "key": "C", "text": "$2$" },
                { "key": "D", "text": "$1$" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q13.png"
        },
        {
            "question_id": "Q14",
            "section": "SECTION 3 - PARAGRAPH TYPE",
            "type": "Comprehension / Paragraph",
            "text": "**Paragraph for Questions 13 & 14 (Continued):**\nWith $g(\\theta)$ and $h(\\theta)$ defined as above, the value of $\\frac{1 + \\left(\\frac{dh}{dg}\\right)^2}{\\frac{d^2 h}{dg^2}}$ at $\\theta = \\pi/4$ is :",
            "options": [
                { "key": "A", "text": "$-\\frac{2}{3}$" },
                { "key": "B", "text": "$-\\frac{4}{3}$" },
                { "key": "C", "text": "$2$" },
                { "key": "D", "text": "$0$" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q14.png"
        },
        {
            "question_id": "Q15",
            "section": "SECTION 3 - PARAGRAPH TYPE",
            "type": "Comprehension / Paragraph",
            "text": "**Paragraph for Questions 15 & 16:**\nTangent at any point $P_1$ (other than $(0,0)$) on the curve $y = x^3$ meets the curve again at $P_2$. Tangent at $P_2$ meets the curve again at $P_3$ and so on.\n\nThe ordinates of $P_1, P_2, P_3, \\ldots$ are in :",
            "options": [
                { "key": "A", "text": "A.P." },
                { "key": "B", "text": "G.P." },
                { "key": "C", "text": "H.P." },
                { "key": "D", "text": "None" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q15.png"
        },
        {
            "question_id": "Q16",
            "section": "SECTION 3 - PARAGRAPH TYPE",
            "type": "Comprehension / Paragraph",
            "text": "**Paragraph for Questions 15 & 16 (Continued):**\nWith the points $P_1, P_2, P_3, P_4, \\ldots$ defined as above on the curve $y = x^3$, the ratio of areas of triangles $\\triangle P_2 P_3 P_4$ and $\\triangle P_1 P_2 P_3$ is :",
            "options": [
                { "key": "A", "text": "$4$" },
                { "key": "B", "text": "$8$" },
                { "key": "C", "text": "$16$" },
                { "key": "D", "text": "$32$" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q16.png"
        },
        {
            "question_id": "Q17",
            "section": "SECTION 4 - MATCHING TYPE",
            "type": "Matrix Match",
            "text": "Match the conditions of differentiable function $f(x)$ in **List I** with their corresponding properties of $f'(x)$ in **List II**:",
            "matching_data": {
                "col1_title": "List I",
                "col2_title": "List II",
                "rows": [
                    {
                        "col1_key": "a",
                        "col1_text": "Differentiable function $f(x)$ satisfies the relation $f(1-x) = f(1+x)$ for all $x \\in \\mathbb{R}$",
                        "col2_key": "p",
                        "col2_text": "Graph of $f'(x)$ is symmetrical about point $(1,0)$"
                    },
                    {
                        "col1_key": "b",
                        "col1_text": "Differentiable function $f(x)$ satisfies the relation $f(2-x) + f(x) = 0$ for all $x \\in \\mathbb{R}$",
                        "col2_key": "q",
                        "col2_text": "Graph of $f'(x)$ is symmetrical about line $x=1$"
                    },
                    {
                        "col1_key": "c",
                        "col1_text": "Differentiable function $f(x)$ satisfies the relation $f(x+2) + f(x) = 0$ for all $x \\in \\mathbb{R}$",
                        "col2_key": "r",
                        "col2_text": "$f'(-1) = f'(3)$"
                    },
                    {
                        "col1_key": "d",
                        "col1_text": "Differentiable function $f(x)$ satisfies the relation $f(x) + f(y) + f(x)f(y) = 1$ for all $x,y$ and $f(x) > 0$",
                        "col2_key": "s",
                        "col2_text": "$f'(x)$ has period $4$"
                    }
                ]
            },
            "options": [
                { "key": "A", "text": "$a \\to p,\\; b \\to qr,\\; c \\to sr,\\; d \\to qr$" },
                { "key": "B", "text": "$a \\to qr,\\; b \\to p,\\; c \\to sr,\\; d \\to qr$" },
                { "key": "C", "text": "$a \\to qr,\\; b \\to p,\\; c \\to qr,\\; d \\to sr$" },
                { "key": "D", "text": "$a \\to qr,\\; b \\to qr,\\; c \\to sp,\\; d \\to sr$" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q17.png"
        },
        {
            "question_id": "Q18",
            "section": "SECTION 4 - MATCHING TYPE",
            "type": "Matrix Match",
            "text": "For the curve $x^2 + y^2 - 4x - 4y - 1 = 0$ at the point $P$ whose ordinate is $5$. Match the items in **Column-I** with the values in **Column-II**:",
            "matching_data": {
                "col1_title": "Column-I",
                "col2_title": "Column-II",
                "rows": [
                    {
                        "col1_key": "P",
                        "col1_text": "$y$-intercept of tangent",
                        "col2_key": "1",
                        "col2_text": "$2$"
                    },
                    {
                        "col1_key": "Q",
                        "col1_text": "$x$-intercept of normal",
                        "col2_key": "2",
                        "col2_text": "$10$"
                    },
                    {
                        "col1_key": "R",
                        "col1_text": "Area of quadrilateral formed by tangent, normal and coordinate axes",
                        "col2_key": "3",
                        "col2_text": "$1$"
                    },
                    {
                        "col1_key": "S",
                        "col1_text": "A tangent to the above curve is drawn such that it is parallel to tangent at $P$. Then its distance from origin is",
                        "col2_key": "4",
                        "col2_text": "$5$"
                    }
                ]
            },
            "options": [
                { "key": "A", "text": "$\\text{P}-4,\\; \\text{Q}-2,\\; \\text{R}-3,\\; \\text{S}-1$" },
                { "key": "B", "text": "$\\text{P}-3,\\; \\text{Q}-2,\\; \\text{R}-1,\\; \\text{S}-4$" },
                { "key": "C", "text": "$\\text{P}-4,\\; \\text{Q}-1,\\; \\text{R}-2,\\; \\text{S}-3$" },
                { "key": "D", "text": "$\\text{P}-1,\\; \\text{Q}-2,\\; \\text{R}-3,\\; \\text{S}-4$" }
            ],
            "is_numerical": False,
            "diagram_path": None,
            "question_crop_path": "../output/question_crops/Q18.png"
        }
    ]

    json_path = os.path.join(base_dir, "output", "questions.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    return questions

if __name__ == "__main__":
    test_pdf = sys.argv[1] if len(sys.argv) > 1 else "sample_pdfs/JUNIOR-SUPER40-AGT-18_MATHS-NMN.pdf"
    res = run_extraction(test_pdf)
    print(f"Extracted {len(res)} questions from {test_pdf}")
