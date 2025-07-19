from flask import redirect, render_template, session
from functools import wraps
from openai import OpenAI
from markdown import markdown as md
import requests

import base64
import os

# Save the last response ID
conversation_memory = {}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HEADERS = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

def ai_query(user_input, web_search=False, reasoning=False, max_output_tokens=4000):
    """Query OpenAI with memory support.

    Returns ``(ai_reply, reasoning_summaries, new_response_id)``. Only supports
    single-user (global memory). ``user_input`` can be a string or a
    list/dict for multimodal input.

    ``web_search``: enable web search tool.
    ``reasoning``: enable o4-mini reasoning mode.
    ``max_output_tokens``: total output/ reasoning tokens when reasoning.
    """
    client = OpenAI()
    previous_response_id = conversation_memory.get('last_response_id')
    try:
        # Detect if user_input is multimodal (list/dict) or plain text
        is_multimodal = isinstance(user_input, (list, dict))
        # Decide model/tools
        if reasoning and web_search:
            model = "o4-mini"
            tools = [{"type": "web_search_preview"}]
            create_kwargs = {
                "model": model,
                "tools": tools,
                "reasoning": {"effort": "medium", "summary": "auto"},
                "max_output_tokens": max_output_tokens,
            }
        elif reasoning:
            model = "o4-mini"
            create_kwargs = {
                "model": model,
                "reasoning": {"effort": "medium", "summary": "auto"},
                "max_output_tokens": max_output_tokens,
            }
        else:
            if web_search:
                model = "gpt-4o-mini"
                tools = [{"type": "web_search_preview"}]
            else:
                model = "gpt-4.1-nano"
                tools = None
            create_kwargs = {"model": model}
            if tools:
                create_kwargs["tools"] = tools
        if previous_response_id:
            create_kwargs["previous_response_id"] = previous_response_id
            if is_multimodal:
                create_kwargs["input"] = user_input
            else:
                create_kwargs["input"] = [{"role": "user", "content": user_input}]
        else:
            create_kwargs["input"] = user_input
        response = client.responses.create(**create_kwargs)
        # Return AI reply and reasoning summary if any
        raw = response.output_text
        ai_reply = md(
            raw,
            extensions=["fenced_code", "codehilite"]
        )
        summaries = []
        for output in getattr(response, "output", []):
            if getattr(output, "type", None) == "reasoning":
                for s in getattr(output, "summary", []):
                    if getattr(s, "type", None) == "summary_text":
                        summaries.append(getattr(s, "text", ""))
        # Save last response id for memory
        conversation_memory['last_response_id'] = response.id
        return ai_reply, raw, summaries, response.id
    except Exception as e:
        return f"[Error]: {e}", "", [], None

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

def ai_query_stream(user_input, history=None):
    """Stream reply text using Chat Completions."""
    client = OpenAI()

    messages = []
    if history:
        for item in history:
            messages.append({"role": "user", "content": item.get("user", "")})
            ai_raw = item.get("ai_raw") or item.get("ai", "")
            messages.append({"role": "assistant", "content": ai_raw})

    messages.append({"role": "user", "content": user_input})

    stream = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=messages,
        stream=True,
    )

    for part in stream:
        delta = part.choices[0].delta.content
        if delta:
            print(repr(delta))
            yield delta

    yield "[DONE]"


def image_generate_stream(prompt):
    """Stream image generation using the Images API."""
    client = OpenAI()

    stream = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024",
        response_format="b64_json",
        stream=True,
    )

    last_b64 = None
    for chunk in stream:
        if chunk.data:
            b64 = chunk.data[0].b64_json
            last_b64 = b64
            print(repr(b64[:10] + "..."))
            yield "data:image/png;base64," + b64

    yield "[DONE]"
    return last_b64

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

def get_fresh_container():
    # If session contains an ID, try it first
    print("🔍 session contents:", session)
    cid = session.get("ci_container_id")
    if cid:
        # Test if this container is still alive
        print("🔍 found ci_container_id in session:", cid)
        try:
            # Hit List files endpoint to "ping" it, 404 will throw
            resp = requests.get(
                f"https://api.openai.com/v1/containers/{cid}/files",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            )
            if resp.status_code == 200:
                return cid
        except requests.HTTPError as e:
            if e.response.status_code != 404:
                raise
        # Expired or non-existent, delete old ID
        session.pop("ci_container_id", None)

    print("🔍 no ci_container_id in session, creating new one")
    # If no valid container_id, create a new one
    resp = requests.post(
        "https://api.openai.com/v1/containers",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={"name": "ci-session"}
    )
    resp.raise_for_status()
    cid = resp.json()["id"]
    session["ci_container_id"] = cid
    print("🔍 saved new ci_container_id to session:", cid)
    return cid



def upload_to_container(container_id, uploaded_file):
    # ── First step：run Files API，register user file as a "File" object
    client = OpenAI()
    file_obj = client.files.create(
        file=(uploaded_file.filename, uploaded_file.stream, uploaded_file.mimetype),
        purpose="user_data"
    )
    file_id = file_obj.id

    # ── Second step：create a JSON to attach it to the container
    url = f"https://api.openai.com/v1/containers/{container_id}/files"
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={"file_id": file_id}
    )
    resp.raise_for_status()
    return resp.json()["id"]  # return container_file_id


def code_interpreter_query(user_input, uploaded_file=None, previous_response_id=None):
    client = OpenAI()
    cid = get_fresh_container()

    if uploaded_file:
        upload_to_container(cid, uploaded_file)

    # Call Responses API, explicitly referencing container
    create_kwargs = {
        "model": "gpt-4.1-nano",
        "tools": [{"type": "code_interpreter", "container": cid}],
        "tool_choice": "required",
        "input": user_input,
    }
    if previous_response_id:
        create_kwargs["previous_response_id"] = previous_response_id
    try:
        response = client.responses.create(**create_kwargs)
    except Exception as e:
        return apology(f"failed to query code interpreter: {str(e)}", 500)

    # Extract text response and all generated files
    output_text = ""
    generated_files = []
    for output in response.output:
        # 1. Normal message text and annotations
        if output.type == "message":
            for c in output.content:
                if getattr(c, "type", None) == "output_text":
                    output_text += getattr(c, "text", "")
                if hasattr(c, "annotations"):
                    for ann in c.annotations:
                        if getattr(ann, "type", None) == "container_file_citation":
                            generated_files.append({
                                "container_id": getattr(ann, "container_id", ""),
                                "file_id": getattr(ann, "file_id", ""),
                                "filename": getattr(ann, "filename", getattr(ann, "file_id", ""))
                            })
        # 2. code_interpreter_call directly generated files
        if output.type == "code_interpreter_call":
            # All kinds of file type fields
            file_fields = [k for k in vars(output) if k.endswith('_path') and getattr(output, k)]
            for field in file_fields:
                file_path = getattr(output, field)
                # Parse container_id and filename
                container_id = getattr(output, 'container_id', '')
                # file_id may not be directly available, use filename as a fallback
                filename = os.path.basename(file_path)
                # file_id may be in path, try to extract it
                file_id = filename
                generated_files.append({
                    "container_id": container_id,
                    "file_id": file_id,
                    "filename": filename
                })
    return output_text, generated_files, getattr(response, "id", None)
