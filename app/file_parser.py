# -*- coding: utf-8 -*-
"""
Spyder Editor

GEN_AI_TOOL project
mrbacco04@gmail.com
Feb 20, 2026

"""

from fastapi import UploadFile
from pypdf import PdfReader
import docx


async def parse_file(file: UploadFile):

    # FIX: ensure filename is string
    filename = file.filename or ""
    name = filename.lower()
    if name.endswith(".txt"):
        content = await file.read()
        return content.decode("utf-8", errors="ignore")
    elif name.endswith(".pdf"):
        reader = PdfReader(file.file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text
    elif name.endswith(".docx"):
        document = docx.Document(file.file)
        return "\n".join(p.text for p in document.paragraphs)
    return ""