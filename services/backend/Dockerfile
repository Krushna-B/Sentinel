FROM public.ecr.aws/lambda/python:3.12

WORKDIR /var/task

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["app.handler.handler"]