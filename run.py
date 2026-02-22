# -*- coding: utf-8 -*-
"""
Spyder Editor

GEN_AI_TOOL project
mrbacco04@gmail.com
Feb 20, 2026

"""

import uvicorn

if __name__ == "__main__":

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )