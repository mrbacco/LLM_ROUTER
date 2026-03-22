"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Q2, 2026

"""

import urllib.request
html = urllib.request.urlopen('http://127.0.0.1:5050/').read().decode('utf-8')
print('Upload & Analyze' in html)
