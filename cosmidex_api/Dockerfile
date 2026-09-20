FROM python:3.14-slim
WORKDIR /app
COPY cosmidex_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY cosmidex_mcp/ ./cosmidex_mcp/
RUN pip install --no-cache-dir ./cosmidex_mcp
COPY cosmidex_api/ .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]