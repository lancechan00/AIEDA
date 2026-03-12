FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /workspace

COPY . /workspace

RUN pip install --upgrade pip && pip install -e .

CMD ["python", "apps/embedding_train_cli.py", "--config", "configs/training/embedding_qwen3_0_6b.yaml"]
