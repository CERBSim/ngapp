# Playwright image already includes Chromium/Firefox/WebKit + OS deps
FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

WORKDIR /app

COPY . .

RUN pip install --upgrade pip \
 && pip install ".[e2e,dev]"

ENV PYTHONPATH=src:.

# If your tests need a display, Playwright can run headless fine.
CMD ["pytest", "-vv", "-s"]
