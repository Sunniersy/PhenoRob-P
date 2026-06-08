ARG BASE_IMAGE_PYTHON=robot-cloud-python-base:3.11-slim
FROM ${BASE_IMAGE_PYTHON}

WORKDIR /app
COPY simulator/requirements.txt /tmp/simulator-requirements.txt
COPY backend/requirements.txt /tmp/backend-requirements.txt
RUN pip install --no-cache-dir -r /tmp/simulator-requirements.txt -r /tmp/backend-requirements.txt
COPY . /app

ENV PYTHONPATH=/app
CMD ["python", "simulator/robot_simulator.py"]
