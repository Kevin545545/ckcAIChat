import datetime
import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from openai import OpenAI

from helpers import apology, ai_query

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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


# In-memory conversation history for each session (for demo, not production)
conversation_memory = {}

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
        ai_reply, _ = ai_query(input_payload)
        if not ai_reply:
            return apology("Failed to process file input", 500)
    else:
        # Query OpenAI without file
        ai_reply, _ = ai_query(user_input)

    # If error, return apology page
    if ai_reply.startswith("[Error]:"):
        return apology(ai_reply[:100], 500)

    # --- Save conversation to memory for history page ---
    history_msgs = conversation_memory.get('messages', [])
    history_msgs.append({"user": user_input, "ai": ai_reply})
    conversation_memory['messages'] = history_msgs

    messages.append({"user": user_input, "ai": ai_reply})
    return render_template("index.html", messages=messages)

@app.route("/history", methods=["GET"])
def history():
    """Display conversation history (single user)."""
    messages = conversation_memory.get('messages', [])

    return render_template("history.html", messages=messages)