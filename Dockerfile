FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY en_core_web_sm-3.8.0-py3-none-any.whl .

RUN pip install /app/en_core_web_sm-3.8.0-py3-none-any.whl
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
RUN chmod -R 777 /app/media