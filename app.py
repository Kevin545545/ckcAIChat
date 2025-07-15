from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from openai import OpenAI

from helpers import apology, ai_query, image_generate, code_interpreter_query

import datetime
import os
import requests
from io import BytesIO

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# In-memory conversation history stored globally for a single user/demo session
conversation_memory = {}

# Store last image response id for multi-turn image generation
image_memory = {}

# Load OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", messages=None)

# Handle chat requests
@app.route("/query", methods=["POST"])
def query():
    user_input = request.form.get("query")
    messages = []

    # If no input, return apology page
    if not user_input:
        return apology("No input provided", 400)

    # Check for OpenAI API key before querying
    if not os.getenv("OPENAI_API_KEY"):
        return apology("OpenAI API key not set", 500)

    # Web search option
    web_search = request.form.get("web_search") == "on"

    # Handle file upload
    client = OpenAI()
    uploaded_file = request.files.get("file")
    file_id = None
    file_name = None
    if uploaded_file and uploaded_file.filename:
        filename = uploaded_file.filename.lower()
        # Check file extension (pdf or image)
        if filename.endswith('.pdf'):
            file_purpose = "user_data"
            file_type = "input_file"
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            file_purpose = "vision"
            file_type = "input_image"
        else:
            return apology("Only PDF or image files are allowed for upload.", 400)
        # Upload file to OpenAI directly from memory
        file_obj = client.files.create(
            file=(uploaded_file.filename, uploaded_file.stream, uploaded_file.mimetype),
            purpose=file_purpose
        )
        file_id = file_obj.id
        file_name = uploaded_file.filename
        file_type_for_input = file_type

    # If file is uploaded, include it in the input
    if file_id:
        input_content = [
            {
                "type": file_type_for_input,
                "file_id": file_id,
            },
            {
                "type": "input_text",
                "text": user_input,
            },
        ]
        input_payload = [
            {
                "role": "user",
                "content": input_content
            }
        ]
        ai_reply, _ = ai_query(input_payload, web_search=web_search)
        if not ai_reply:
            return apology("Failed to process file input", 500)
    else:
        # Query OpenAI without file
        ai_reply, _ = ai_query(user_input, web_search=web_search)

    # If error, return apology page
    if ai_reply.startswith("[Error]:"):
        return apology(ai_reply[:100], 500)

    # --- Save conversation to memory for history page ---
    history_msgs = conversation_memory.get('messages', [])
    history_msgs.append({"user": user_input, "ai": ai_reply})
    conversation_memory['messages'] = history_msgs

    messages.append({"user": user_input, "ai": ai_reply})
    return render_template("index.html", messages=messages)

@app.route("/generate_image", methods=["POST", "GET"])
def generate_image():

    if request.method == "GET":
        return render_template("image.html")

    prompt = request.form.get("image_prompt")
    if not prompt:
        return apology("No prompt provided", 400)
    prev_id = image_memory.get("last_image_response_id")
    try:
        # Generate image using OpenAI Responses API
        file_path, filename, response_id = image_generate(prompt, previous_response_id=prev_id)
        if not file_path:
            return apology("Image generation failed", 500)
    except Exception as e:
        return apology(f"Image generation failed: {str(e)}", 500)
    # Save last image response id for follow-up
    image_memory["last_image_response_id"] = response_id
    # Append the new image message to the full conversation history
    history_msgs = conversation_memory.get('messages', [])
    history_msgs.append({"user": prompt, "ai": f'<img src="/temp_files/{filename}" alt="generated image" style="max-width:400px;">' })
    conversation_memory['messages'] = history_msgs

    # Only show image messages in the image page
    image_msgs = [msg for msg in history_msgs if '<img' in msg.get('ai', '')]
    return render_template("image.html", messages=image_msgs)

@app.route("/temp_files/<filename>")
def serve_temp_file(filename):
    """Serve files from the temp_files directory."""
    from flask import send_from_directory
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_files")
    return send_from_directory(temp_dir, filename)

@app.route("/history", methods=["GET"])
def history():
    """Display conversation history (single user), including image messages."""
    messages = conversation_memory.get('messages', [])
    # Ensure image messages are included (already appended in generate_image)
    return render_template("history.html", messages=messages)

@app.route("/code_interpreter", methods=["GET", "POST"])
def code_interpreter():
    messages = []
    generated_files = []
    if request.method == "POST":
        user_input = request.form.get("ci_query")
        uploaded_file = request.files.get("ci_file")
        prev_id = session.get("ci_last_response_id")
        
        try:
            output_text, files, response_id = code_interpreter_query(user_input, uploaded_file, previous_response_id=prev_id)
        except Exception as e:
            return apology(f"Code interpreter query failed: {str(e)}", 500)
        print(f"测试到底有没有文件：{files}")
        session["ci_last_response_id"] = response_id

        # --- Save conversation to memory for history page ---
        history_msgs = conversation_memory.get('messages', [])
        history_msgs.append({"user": user_input, "ai": output_text})
        conversation_memory['messages'] = history_msgs
        messages.append({"user": user_input, "ai": output_text})
        generated_files = files
    return render_template("code_interpreter.html", messages=messages, generated_files=generated_files)

@app.route("/download_ci_file/<container_id>/<file_id>/<filename>")
def download_ci_file(container_id, file_id, filename):
    client = OpenAI()
    try:
        url = f"https://api.openai.com/v1/containers/{container_id}/files/{file_id}/content"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return send_file(
                BytesIO(resp.content),
                as_attachment=True,
                download_name=filename,
                mimetype="application/octet-stream"
            )
    except Exception as e:
        return apology(f"Failed to download file: {str(e)}", 500)