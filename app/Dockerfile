FROM ubuntu:23.10

WORKDIR /code


RUN apt update && apt install -y python3 python3-pip python3-venv

#&& python3 -m pip install --upgrade pip \

COPY requirements.txt /code/requirements.txt
RUN python3 -m venv venv && \
     . venv/bin/activate && \
     pip install -r /code/requirements.txt

COPY . /code/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OPENAI_API_KEY=openai_api_token


CMD ["venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]

