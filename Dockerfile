FROM mcr.microsoft.com/playwright/python:v1.49.0-noble
WORKDIR /app
COPY requirements-cli.txt .
RUN pip install --no-cache-dir "setuptools<70" -r requirements-cli.txt
COPY . ./
RUN mkdir -p /output
ENTRYPOINT ["python", "-m", "cli.main"]
CMD ["--help"]
