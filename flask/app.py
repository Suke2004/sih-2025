from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS, cross_origin
import os
from gtts import gTTS
import google.generativeai as genai
from threading import Thread
from markdown_it import MarkdownIt
from markdown_it.token import Token
from typing import List
import re

# Flask app
app = Flask(__name__)
CORS(app, origins=["*"])
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["AUDIO_FOLDER"] = "audio"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["AUDIO_FOLDER"], exist_ok=True)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are an expert agricultural advisor for farmers in Punjab, India. 
You will be given a soil test report as an input image or document.

Your tasks:
1. Carefully analyze the soil test parameters (pH, organic matter, nitrogen, phosphorus, potassium, micronutrients, etc.).
2. Based on the soil quality and conditions in Punjab, suggest the top 3 best crops suitable for cultivation.
3. For each crop:
   - Provide a detailed farming plan from planting to harvesting.
   - Include requirements for soil preparation, seed selection, fertilizers, irrigation, pest/disease management, and harvesting timeline.
   - Consider Punjab’s local weather conditions and seasonal variations.
   - Add expected yield potential and possible risks.
   - If available, summarize current or recent market price trends for that crop in Punjab.
4. Present the answer in the language specified by the user (Hindi, Punjabi, or English).
5. Keep the explanation clear, structured, and practical so that a farmer can easily follow it for planning.
6. Farmers dont know the technicality to use the local language to make them easier to understand.
If information is uncertain (such as exact price trends), give an approximate explanation with reasoning instead of skipping it.
Respond in {LANGUAGE}
"""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze-image/", methods=["POST"])
def analyze_image():
    if "soil_report" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["soil_report"]
    language = request.form.get("language", "English")
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    # Gemini model
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
        [SYSTEM_PROMPT.replace("{LANGUAGE}", language),
         {"mime_type": "image/jpeg", "data": open(filepath, "rb").read()}]
    )
    markdown_response = response.text
    
    # New robust section-splitting logic
    sections_list = []
    
    # Find all headings (e.g., `#`, `##`) and their positions
    headings = list(re.finditer(r'^#+\s*([^\n]+)', markdown_response, re.MULTILINE))
    
    # Handle the initial "Overall Analysis" section if it exists before the first heading
    start_pos = 0
    if headings:
        first_heading_pos = headings[0].start()
        if first_heading_pos > 0:
            preamble_content = markdown_response[start_pos:first_heading_pos].strip()
            if preamble_content:
                sections_list.append({
                    "title": "Overall Analysis",
                    "content": markdown_to_plain_text(preamble_content)
                })
        start_pos = first_heading_pos

    # Iterate through headings to create sections
    for i, heading in enumerate(headings):
        end_pos = headings[i+1].start() if i + 1 < len(headings) else len(markdown_response)
        
        title = heading.group(1).strip()
        content = markdown_response[heading.start():end_pos].strip()
        
        # We need to remove the heading from the content for clean text
        content_without_heading = content.replace(heading.group(0), "", 1).strip()
        
        sections_list.append({
            "title": title,
            "content": markdown_to_plain_text(content_without_heading)
        })

    # If no headings are found, treat the whole response as a single section
    if not sections_list and markdown_response:
        sections_list.append({
            "title": "Analysis Result",
            "content": markdown_to_plain_text(markdown_response)
        })

    # Prepare audio filename
    base_filename = os.path.splitext(file.filename)[0]
    results = []

    def generate_audio_for_section(text, lang_code, section_index):
        audio_filename = f"response_{base_filename}_part_{section_index}.mp3"
        audio_path = os.path.join(app.config["AUDIO_FOLDER"], audio_filename)
        tts = gTTS(text=text, lang=lang_code)
        tts.save(audio_path)
        return f"/get-audio/{audio_filename}"

    lang_code = {"English": "en", "Hindi": "hi", "Punjabi": "pa"}.get(language, "en")

    threads = []
    for i, section in enumerate(sections_list):
        results.append({
            "title": section["title"],
            "text": section["content"],
            "audio_url": ""
        })
        
        thread_args = (section["content"], lang_code, i)
        thread = Thread(target=lambda: results[i].update({"audio_url": generate_audio_for_section(*thread_args)}))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return jsonify(results)

@app.route("/get-audio/<filename>")
def get_audio(filename):
    return send_from_directory(app.config["AUDIO_FOLDER"], filename)

# --- Markdown to Plain Text Conversion Function ---
def markdown_to_plain_text(md_text: str) -> str:
    """
    Converts Markdown formatted text to clean, plain text while preserving
    structural elements like headings, lists, and paragraphs.
    """
    md = MarkdownIt()
    tokens = md.parse(md_text)
    
    plain_text_parts = []
    
    for token in tokens:
        if token.type == 'text':
            plain_text_parts.append(token.content)
        elif token.type == 'inline':
            for child in token.children:
                if child.type == 'text':
                    plain_text_parts.append(child.content)
                elif child.type == 'softbreak':
                    plain_text_parts.append(' ')
                elif child.type == 'hardbreak':
                    plain_text_parts.append('\n')
        elif token.type == 'softbreak':
            plain_text_parts.append(' ')
        elif token.type == 'hardbreak':
            plain_text_parts.append('\n')
        elif token.type == 'paragraph_close' or token.type == 'heading_close':
            plain_text_parts.append('\n\n')
        elif token.type == 'list_item_open':
            plain_text_parts.append('\n')
        elif token.type == 'fence' or token.type == 'code_block':
            plain_text_parts.append(token.content)
            plain_text_parts.append('\n\n')
            
    result = "".join(plain_text_parts)
    return os.linesep.join([s for s in result.splitlines() if s.strip()]).strip()

if __name__ == "__main__":
    app.run(debug=True)