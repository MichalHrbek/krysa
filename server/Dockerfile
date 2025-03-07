FROM python:3.12.9

EXPOSE 8000

WORKDIR /usr/src/krysa
COPY ./c2/ ./
COPY ./dashboard/dist ./dashui

RUN pip install --no-cache-dir -r requirements.txt

CMD ["fastapi", "run", "--port", "8000"]
