#!/bin/bash
docker build -t clip-crawler .
docker run -it -v "$(pwd)/output:/app/output" clip-crawler 