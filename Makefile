
build:
	gcc -shared -fpic -o shm_lib_$(shell uname -s | tr A-Z a-z).so shm/v2/shm_lib.c

run-c:
	gcc -o main main.c
	./main
	rm main

run-python: build
	python3 main.py
	rm shm_lib_$(shell uname -s | tr A-Z a-z).so