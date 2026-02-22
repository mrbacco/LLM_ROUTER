# -*- coding: utf-8 -*-
"""
Spyder Editor

GEN_AI_TOOL project
mrbacco04@gmail.com
Feb 20, 2026

"""

from sqlalchemy import Column, Integer, Text
from app.database import Base


class ChatMessage(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    model = Column(Text)
    role = Column(Text)
    content = Column(Text)