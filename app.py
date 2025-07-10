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
        # Check file extension (must be .pdf)
        if not uploaded_file.filename.lower().endswith('.pdf'):
            return apology("Only PDF files are allowed for upload.", 400)
        # Create a temp directory under Project if not exists
        temp_dir = os.path.join(os.path.dirname(__file__), "temp_files")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        # Save the uploaded file temporarily in temp_files
        temp_path = os.path.join(temp_dir, uploaded_file.filename)
        uploaded_file.save(temp_path)
        # Upload file to OpenAI
        file_obj = client.files.create(
            file=open(temp_path, "rb"),
            purpose="user_data"
        )
        file_id = file_obj.id
        file_name = uploaded_file.filename

    # If file is uploaded, include it in the input
    if file_id:
        input_content = [
            {
                "type": "input_file",
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
        response = client.responses.create(
            model="gpt-4.1-nano",
            input=input_payload
        )
        ai_reply = response.output_text
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