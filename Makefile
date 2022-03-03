.PHONY: generate-tag-shims

generate-tag-shims: 
	poetry run python generate.py
