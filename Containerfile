FROM python:3.9-alpine
COPY . /app
WORKDIR /app
RUN apk update; \
    apk add doxygen;\
    apk add libxslt
RUN pip install .
ENTRYPOINT ["dlg_paletteGen"]
