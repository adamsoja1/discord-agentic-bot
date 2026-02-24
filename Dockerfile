FROM python:3.11-slim

WORKDIR /app

# Install git (needed for GitHub-based pip packages)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install litellm[proxy]
ENV PYTHONUNBUFFERED=1

CMD ["python3", "-m", "src.discord.app"]
