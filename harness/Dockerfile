FROM python:3.12-slim
WORKDIR /app
COPY harness/harness ./harness
RUN pip install --no-cache-dir fastapi uvicorn httpx
EXPOSE 8098
CMD ["python", "-m", "harness"]
