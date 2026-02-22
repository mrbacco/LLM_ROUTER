# -*- coding: utf-8 -*-
"""
Spyder Editor

GEN_AI_TOOL project
mrbacco04@gmail.com
Feb 20, 2026

"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = "sqlite+aiosqlite:///data/chat.db"

engine = create_async_engine(DATABASE_URL)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()