import streamlit as st
import json
import requests
import fitz  
import docx
import mimetypes
import email
from bs4 import BeautifulSoup
from PIL import Image
import io
import re
import easyocr

# Initialize EasyOCR
ocr = easyocr.Reader(['en'], gpu=False)

# Title
st.title(" Unstructured Text to Structured JSON Extractor")
st.markdown("Upload your **schema** and **unstructured input** (text, PDF, DOCX, HTML, EML, or image-based PDFs). The app will extract structured JSON as per schema.")

# Upload schema and input file
schema_file = st.file_uploader("Upload JSON Schema", type="json")
text_file = st.file_uploader("Upload Input File (any format)")

# Model selector and OpenRouter API key input
model_choice = "mistralai/mistral-7b-instruct"
api_key = st.secrets["OPENROUTER_API_KEY"]
# Complexity analysis
@st.cache_data
def analyze_schema_complexity(schema):
    def traverse(obj, level=1):
        fields, enums, max_level = 0, 0, level
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "enum" and isinstance(v, list):
                    enums += len(v)
                elif k == "properties":
                    fields += len(v)
                    for sub in v.values():
                        f, l, e = traverse(sub, level + 1)
                        fields += f; enums += e; max_level = max(max_level, l)
                elif isinstance(v, (dict, list)):
                    f, l, e = traverse(v, level + 1)
                    fields += f; enums += e; max_level = max(max_level, l)
        elif isinstance(obj, list):
            for item in obj:
                f, l, e = traverse(item, level + 1)
                fields += f; enums += e; max_level = max(max_level, l)
        return fields, max_level, enums

    fields, depth, enums = traverse(schema)
    score = fields + 5 * depth + 0.01 * enums
    return fields, depth, enums, round(score, 2)

def strategy_selector(score):
    if score < 100:
        return "Direct prompt, no schema splitting"
    elif score < 200:
        return "Chunked schema or input, 2–3 LLM calls"
    else:
        return "Chunk schema & input, iterative stitching"

# Prompt generator based on strategy

def generate_prompt(schema, input_text, strategy):
    base_prompt = "You are an expert system for structuring unstructured data. Your task is to convert the provided text into a structured JSON format that follows the exact schema below."
    schema_json = json.dumps(schema, indent=2)

    if strategy == "Direct prompt, no schema splitting":
        return f"{base_prompt}\n\nSchema:\n{schema_json}\n\nInput Text:\n{input_text}\n\nReturn ONLY the extracted JSON."

    elif strategy == "Chunked schema or input, 2–3 LLM calls":
        return f"{base_prompt}\n\nDue to size, you may only see part of the schema or input. Ensure strict adherence to the schema below.\n\nSchema (partial or full):\n{schema_json}\n\nInput Text:\n{input_text}\n\nReturn JSON matching the schema."

    elif strategy == "Chunk schema & input, iterative stitching":
        return f"{base_prompt}\n\nSchema is complex. Apply an iterative approach to structure the input across schema segments. Maintain exact property names.\n\nSchema (may be partial):\n{schema_json}\n\nInput Text (chunk):\n{input_text}\n\nReturn valid JSON output."

# File readers

def extract_text(file):
    name = file.name.lower()
    mime_type, _ = mimetypes.guess_type(file.name)

    if name.endswith(".pdf"):
        try:
            doc = fitz.open(stream=file.read(), filetype="pdf")
            text = "\n".join(page.get_text() for page in doc)
            if not text.strip():
                ocr_text = []
                for page in doc:
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format='PNG')
                    result = ocr.readtext(img_bytes.getvalue())
                    for _, text, _ in result:
                        ocr_text.append(text)
                text = "\n".join(ocr_text)
            return text
        except Exception as e:
            return f"Error reading PDF: {e}"

    elif name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])

    elif name.endswith(".eml"):
        msg = email.message_from_bytes(file.read())
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode(errors="ignore")
                elif part.get_content_type() == "text/html":
                    soup = BeautifulSoup(part.get_payload(decode=True), "html.parser")
                    return soup.get_text()
        else:
            return msg.get_payload(decode=True).decode(errors="ignore")

    elif name.endswith(".html") or mime_type == "text/html":
        soup = BeautifulSoup(file.read(), "html.parser")
        return soup.get_text()

    else:
        return file.read().decode("utf-8", errors="ignore")

# Query OpenRouter API with structured messages

def query_openrouter_contextual(prompt, model, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://metaform-demo.streamlit.app/",
        "Content-Type": "application/json"
    }
    messages = [
        {"role": "system", "content": "You convert unstructured content into strict JSON format given a schema."},
        {"role": "user", "content": prompt}
    ]
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json={"model": model, "messages": messages})
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def extract_json_from_text(text):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        else:
            raise ValueError("No valid JSON object found in the response.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")

if schema_file and text_file and st.button("Generate JSON"):
    if not api_key:
        st.warning(" Please enter your OpenRouter API key to proceed.")
    else:
        schema = json.load(schema_file)
        text = extract_text(text_file)

        fields, depth, enums, score = analyze_schema_complexity(schema)
        strategy = strategy_selector(score)

        st.subheader("Schema Complexity Analysis")
        st.json({
            "Total Fields": fields,
            "Nesting Depth": depth,
            "Enum Count": enums,
            "Complexity Score": score,
            "Recommended Strategy": strategy
        })

        st.subheader(" Input Text")
        st.text_area("View Text Input", text, height=200)

        with st.spinner("Calling model via OpenRouter with schema & text in context..."):
            try:
                prompt = generate_prompt(schema, text, strategy)
                st.subheader("🧾 Prompt Sent to LLM")
                st.code(prompt, language="markdown")

                output = query_openrouter_contextual(prompt, model=model_choice, api_key=api_key)
                parsed = extract_json_from_text(output)
                st.success("JSON Extracted")
                st.json(parsed)

                json_bytes = json.dumps(parsed, indent=2).encode('utf-8')
                st.download_button(
                    label="📥 Download JSON Output",
                    data=json_bytes,
                    file_name="extracted_output.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f" Error during extraction: {e}")
                st.text(output if 'output' in locals() else "No output returned.")
else:
    st.info("Please upload both a schema file and a text file to begin. Then click 'Generate JSON'.")

