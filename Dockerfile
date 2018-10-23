FROM python:3.5-slim
ENV PYTHONUNBUFFERED 1
# For cache
RUN mkdir /app
WORKDIR /app
ADD requirements.txt requirements_test.txt /app/
RUN pip install --trusted-host pypi.python.org -r requirements_test.txt

ADD . /app
COPY adock/settings_docker.py /app/adock/settings_local.py

# EXPOSE 8000
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
