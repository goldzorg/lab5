FROM brunneis/python:3.8.3-ubuntu-20.04
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
EXPOSE 3000
ENTRYPOINT ["python3"]
CMD ["scanner.py"]
