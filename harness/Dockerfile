# Harness — continuous same-AZ small-object bakeoff
#
# Reads EXPRESS_BUCKET and STANDARD_BUCKET from the environment, issues
# concurrent GETs against a fixed key set, records latencies, and serves a
# built-in dashboard on :8080.
#
# Designed to run on EC2 in the same AZ as the directory bucket (apse2-az1).

FROM public.ecr.aws/docker/library/python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py dash.html ./

ENV HARNESS_PORT=8080 \
    OBJECT_PREFIX=hot/ \
    OBJECT_COUNT=64 \
    OBJECT_SIZE_BYTES=16384 \
    LOOP_SLEEP_MS=50 \
    WINDOW_SECONDS=300

EXPOSE 8080

CMD ["python", "-u", "app.py"]
