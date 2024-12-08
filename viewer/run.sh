#!/bin/bash
python3 manage.py runserver & npx tailwindcss -i ./static/src/input.css -o ./static/src/output.css --watch