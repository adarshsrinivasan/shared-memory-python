
build:
	gcc -shared -fpic -o shm_lib_$(shell uname -s | tr A-Z a-z).so shm/v2/shm_lib.c
	chmod 777 shm_lib_$(shell uname -s | tr A-Z a-z).so

build-docker:
	docker build -t adarshzededa/shm-py .

run-c:
	gcc -o main main.c
	./main
	rm main

run-python: build
	python3 main.py
	rm shm_lib_$(shell uname -s | tr A-Z a-z).so

run-docker: build-docker
	docker run -d --user 999:999 --ipc host --name shm-client1 -p 50000:50000 adarshzededa/shm-py:latest
	#docker run -d --user 998:998 --ipc host --name shm-client2 -p 50001:50000 adarshzededa/shm-py:latest