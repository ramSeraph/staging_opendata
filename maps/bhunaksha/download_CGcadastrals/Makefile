all : download.py
	python3 download.py --headless | tee log$(date +%F%T).txt

gui:
	python3 download.py | tee log$(date +%F%T).txt
