"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Feb 21, 2026

"""

import json
import os
import threading


MEMORY_FILE = "memory.json"
MEMORY_LOCK = threading.RLock()


def load_all():

    with MEMORY_LOCK:
        if not os.path.exists(MEMORY_FILE):

            return {}

        with open(MEMORY_FILE) as f:

            return json.load(f)


def save_all(data):

    with MEMORY_LOCK:
        with open(MEMORY_FILE, "w") as f:

            json.dump(data, f)


def save_message(model, role, content):

    with MEMORY_LOCK:
        data = load_all()

        if model not in data:

            data[model] = []

        data[model].append({

            "role": role,

            "content": content

        })

        save_all(data)


def save_message_and_get_memory(model, role, content, limit=None):

    with MEMORY_LOCK:
        data = load_all()

        if model not in data:
            data[model] = []

        data[model].append({
            "role": role,
            "content": content
        })

        save_all(data)

        messages = data.get(model, [])

        if limit and limit > 0:
            return messages[-limit:]

        return messages


def load_memory(model, limit=None):

    data = load_all()

    messages = data.get(model, [])

    if limit and limit > 0:
        return messages[-limit:]

    return messages
