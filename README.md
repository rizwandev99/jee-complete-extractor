# ⚡ JEE Complete Extractor & Diagram Cropping Engine

[![Render](https://img.shields.io/badge/Render-Live-success?style=flat-square&logo=render)](https://jee-complete-extractor.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

An enterprise-grade, automated engine designed to digitize IIT-JEE question papers with sub-pixel diagram cropping, mathematical KaTeX LaTeX formatting, handwritten scribble noise removal, and native structured table generation.

👉 **[Live Web Application (24/7)](https://jee-complete-extractor.onrender.com)**

---

## 🌟 Key Highlights

- 🎯 **Dual-Track Diagram Cropping:** Detects Physics raster diagrams and Chemistry vector drawings with sub-pixel bounding box accuracy.
- ✍️ **Handwritten Scribble Elimination:** Strict noise filter strips out students' pen marks, red/blue scratches, rough work, and pencil doodles.
- 📱 **Responsive Cyber Terminal UI:** Dark-mode Linear/Cyberpunk aesthetic optimized for Desktop, Tablet, and Mobile viewport sizes.
- 📊 **Native Structured Tables:** Extracts match matrices and lists into clean, native HTML/Markdown tables instead of pixelated image crops.
- 🛡️ **Zero-Failure Hybrid Pipeline:** Mistral AI LaTeX polish with instant PyMuPDF native fallback for rock-solid reliability.

---

## 🏗️ Architecture

```
+-------------------------------------------------------------+
|                     JEE Question PDF                        |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|               PyMuPDF Text & Vector Extractor               |
|  - Blocks & Span Font Analysis                              |
|  - Vector Drawing Path Clustering (Curves, Lines, Meshes)   |
|  - Embedded Raster Image Extraction                         |
+-------------------------------------------------------------+
                               |
            +------------------+------------------+
            |                                     |
            v                                     v
+-----------------------+             +-----------------------+
|  Question Segmenter   |             | Scribble Noise Filter |
|  - Question Numbering |             | - Rough Work Stripper |
|  - Options (A, B, C,D)|             | - Handwritten Marks   |
|  - Numerical Inputs   |             | - Margin Doodles      |
+-----------------------+             +-----------------------+
            |                                     |
            +------------------+------------------+
                               |
                               v
+-------------------------------------------------------------+
|                 Mistral AI Polish & LaTeX                   |
|  - Mathematical KaTeX Equation Conversion ($...$, $$...$$)  |
|  - Native Matching Table Structuring (List I / List II)     |
|  - Zero-Failure Instant Local Fallback                      |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|            FastAPI REST Server & Cyber Deck UI              |
|  - Full Question Bounding Box Snippets (PNG)                |
|  - Isolated Diagram Crops (PNG)                             |
|  - Structured Question JSON Database                        |
+-------------------------------------------------------------+
```

---

## 🚀 Quick Start (Local Setup)

### Prerequisites
- Python 3.10 or 3.11
- `git`

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rizwandev99/jee-complete-extractor.git
   cd jee-complete-extractor
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables (Optional):**
   ```bash
   cp .env.example .env
   # Edit .env to add your MISTRAL_API_KEY if desired
   ```

5. **Start the server:**
   ```bash
   python server.py
   ```
   Open [http://localhost:7860](http://localhost:7860) (or the port specified by `PORT`) in your browser.

---

## 🐳 Docker Deployment

Run locally or on any cloud container service using Docker:

```bash
# Build the Docker image
docker build -t jee-extractor .

# Run container on port 7860
docker run -p 7860:7860 jee-extractor
```

Access the application at [http://localhost:7860](http://localhost:7860).

---

## ☁️ Deploy to Render in 1 Click

You can deploy your own 24/7 hosted instance to Render using the Blueprint:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/rizwandev99/jee-complete-extractor)

---

## 📡 API Reference

| Endpoint | Method | Description | Request Payload / Params | Response |
|---|---|---|---|---|
| `/` | `GET` | Serves the interactive Cyber Terminal Web Dashboard | None | HTML |
| `/api/upload-pdf` | `POST` | Uploads a JEE PDF and triggers extraction pipeline | `multipart/form-data` (`file`) | JSON (`status`, `count`, `questions`) |
| `/api/questions` | `GET` | Returns list of currently extracted questions | None | JSON array of question objects |
| `/api/clear-all` | `POST` | Resets database, wipes uploads, and clears generated crops | None | JSON confirmation message |

---

## 📋 Data Schema

Each extracted question returned by `/api/questions` conforms to the following schema:

```json
{
  "id": 5,
  "number": "5",
  "section": "SECTION 1 (Maximum Marks: 12)",
  "type": "Single Correct",
  "is_numerical": false,
  "text": "An inverted cone of base radius $10\\text{ cm}$...",
  "options": [
    { "key": "A", "text": "Option text with math formula" },
    { "key": "B", "text": "Option text with math formula" },
    { "key": "C", "text": "Option text with math formula" },
    { "key": "D", "text": "Option text with math formula" }
  ],
  "table_html": null,
  "diagram_url": "/output/diagrams/Q5_diagram.png",
  "snippet_url": "/output/question_crops/Q5.png"
}
```

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).
