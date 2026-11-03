FROM python:3.12-slim
WORKDIR /opt/assurance-lab
COPY src ./src
COPY common.py ./common.py
COPY ARQA ./ARQA
ENV PYTHONPATH=/opt/assurance-lab/src:/opt/assurance-lab
CMD ["python", "ARQA/run_arqa_v3.py"]
