# -*- coding: utf-8 -*-
"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Q2, 2026

"""

from sqlalchemy import Column, Integer, Text
from app.database import Base


class ChatMessage(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    model = Column(Text)
    role = Column(Text)
    content = Column(Text)