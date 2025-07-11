from flask import redirect, render_template, session
from functools import wraps
from openai import OpenAI
import requests

import base64
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

def image_generate(prompt, previous_response_id=None):
    """
    Generate an image using OpenAI Responses API, save to temp_files, return file path and base64.
    """
    client = OpenAI()
    # Ensure temp_files dir exists
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_files")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    # Prepare API call
    kwargs = {
        "model": "gpt-4.1-nano",
        "input": prompt,
        "tools": [{"type": "image_generation", "quality": "low", "moderation": "low"}],
    }
    if previous_response_id:
        kwargs["previous_response_id"] = previous_response_id
    response = client.responses.create(**kwargs)
    image_data = [output.result for output in response.output if output.type == "image_generation_call"]
    if image_data:
        image_base64 = image_data[0]
        # Save image to temp_files
        filename = f"generated_{response.id}.png"
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(image_base64))
        return file_path, filename, response.id
    return None, None, response.id

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