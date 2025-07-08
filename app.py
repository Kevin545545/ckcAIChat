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

    # Call the helper function to get AI reply and manage memory (no user_id)
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