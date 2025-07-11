from flask import redirect, render_template, session
from functools import wraps
from openai import OpenAI
import requests

import os

# Save the last response ID
conversation_memory = {}


def ai_query(user_input):
    """
    Query OpenAI with memory support. Returns (ai_reply, new_response_id).
    Only supports single-user (global memory).
    user_input can be a string (text) or a list/dict (multi-modal input).
    """
    client = OpenAI()
    previous_response_id = conversation_memory.get('last_response_id')
    try:
        # Detect if user_input is multimodal (list/dict) or plain text
        is_multimodal = isinstance(user_input, (list, dict))
        if previous_response_id:
            if is_multimodal:
                # If already a list, just pass it through
                response = client.responses.create(
                    model="gpt-4.1-nano",
                    previous_response_id=previous_response_id,
                    input=user_input,
                )
            else:
                response = client.responses.create(
                    model="gpt-4.1-nano",
                    previous_response_id=previous_response_id,
                    input=[{"role": "user", "content": user_input}],
                )
        else:
            response = client.responses.create(
                model="gpt-4.1-nano",
                input=user_input,
            )
        ai_reply = response.output_text
        # Save last response id for memory
        conversation_memory['last_response_id'] = response.id
        return ai_reply, response.id
    except Exception as e:
        return f"[Error]: {e}", None



def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code