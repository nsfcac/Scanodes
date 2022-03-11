
init:
	@echo "Create virtural environment..."
	@-python3 -m venv env; \
	. ./env/bin/activate; \
	pip install -r requirements.txt; \
	python3 -m pip install --upgrade pip