index:
	uv run scripts/generate_index.py

validate:
	python3 -c "import json; json.load(open('index.json'))"

.PHONY: index validate
