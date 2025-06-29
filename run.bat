@echo off
docker build -t clip-crawler .
docker run -it -v "%cd%\output:/app/output" clip-crawler

