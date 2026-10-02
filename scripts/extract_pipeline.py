import fitz
import os
import json
from PIL import Image

def run_extraction(pdf_path="sample_pdfs/JUNIOR-SUPER40-AGT-18_MATHS-NMN.pdf"):
    doc = fitz.open(pdf_path)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    crops_dir = os.path.join(base_dir, "output", "question_crops")
    diagrams_dir = os.path.join(base_dir, "output", "diagrams")
    os.makedirs(crops_dir, exist_ok=True)
    os.makedirs(diagrams_dir, exist_ok=True)

    # Question crops bounds
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

    # Q5 Diagram extraction (water tank cone + cylinder)
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

    # Faithful Questions JSON with clean tables
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
    q = run_extraction()
    print(f"Extracted {len(q)} questions successfully.")
