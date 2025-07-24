# 🔄 Unstructured Text to Structured JSON Extractor

A Streamlit web app to convert **unstructured files** (text, PDF, DOCX, HTML, EML, scanned images, etc.) into **structured JSON output** using a user-supplied schema and a Large Language Model via [OpenRouter](https://openrouter.ai).

---

## 🚀 Features

- 📤 Accepts various unstructured formats:
  - `.txt`, `.pdf`, `.docx`, `.html`, `.eml`, `.bib`, and scanned image-based PDFs.
- 📦 Upload custom **JSON schemas** with 3–7 levels of nesting, enums, and deeply nested objects.
- 🧠 Automatically analyzes schema complexity and selects the most efficient extraction strategy:
  - Direct Prompt
  - Chunked Schema/Input
  - Iterative Stitching
- 💬 Uses [OpenRouter](https://openrouter.ai) to call open-source LLMs like **Mistral**, **LLaMA**, and **Mixtral**.
- 🧾 Shows the **exact prompt** sent to the model.
- ✅ JSON is auto-parsed, previewed, and available for **download**.

---

## 🧪 How It Works

1. **Schema Complexity Scoring**:
   ```python
   score = num_fields + 5 * depth + 0.01 * num_enums
   ```
   - < 100 → Direct Prompt  
   - 100–200 → Chunked Input or Schema  
   - > 200 → Iterative Stitching  

2. **Prompt is dynamically generated** based on:
   - Schema
   - Text content
   - Chosen strategy

3. **LLM call via OpenRouter**: Model processes the prompt and returns structured output.

4. **Postprocessing**:
   - Extracts JSON block from output
   - Validates format
   - Allows download

---

## 🖼️ UI Walkthrough

1. **Upload JSON schema**
2. **Upload unstructured document** (any supported format)
3. **Enter OpenRouter API key**
4. **Select model** (Mistral 7B, Mixtral, LLaMA 13B)
5. **Click "Generate JSON"**
6. View:
   - Schema complexity metrics
   - Raw input
   - Generated prompt
   - Final extracted JSON
7. **Download** the structured JSON

---

## 📦 Installation

### Step 1: Clone and install dependencies

```bash
git clone https://github.com/your-username/json-extractor-app.git
cd json-extractor-app
pip install -r requirements.txt
```

### Step 2: Run the app

```bash
streamlit run app.py
```

---

## 📄 requirements.txt

```txt
streamlit
requests
pymupdf
python-docx
beautifulsoup4
pillow
easyocr
```

---

## 🔐 OpenRouter Setup

1. Get your API key from [https://openrouter.ai](https://openrouter.ai)
2. Enter it directly in the app or save it in `.streamlit/secrets.toml` like this:

```toml
OPENROUTER_API_KEY = "your-key-here"
```

---

## 📁 File Support

| Format | Supported | Notes |
|--------|-----------|-------|
| `.json` | ✅ | Schema only |
| `.txt` | ✅ | Unstructured text |
| `.pdf` | ✅ | Text & scanned (via OCR) |
| `.docx` | ✅ | Native Word files |
| `.html` | ✅ | Extracts visible text |
| `.eml` | ✅ | Plaintext or HTML body |
| `.bib` | ✅ | Parsed as text |
| Image-based PDF | ✅ | Uses EasyOCR |

---

## 🛠️ Future Improvements

- Multi-file stitching
- Feedback-based refinement
- HuggingFace or LangChain support
- Native schema validator

---

## 🧑‍💻 Contributing

Pull requests welcome!  
You can also submit issues or suggestions.

---

## 📄 License

[MIT License](LICENSE)

---

## 🙌 Credits

Built with:
- 🧠 [OpenRouter](https://openrouter.ai)
- 📘 [Streamlit](https://streamlit.io)
- 👁️ [EasyOCR](https://github.com/JaidedAI/EasyOCR)
