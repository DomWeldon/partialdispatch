.PHONY:repl
repl:
	pdm run bpython


.PHONY:repl38
repl38:
	pdm multirun -i 3.8 pdm run bpython

.PHONY:repl39
repl39:
	pdm multirun -i 3.9 pdm run bpython

.PHONY:repl310
repl310:
	pdm multirun -i 3.10 pdm run bpython

.PHONY:repl311
repl311:
	pdm multirun -i 3.11 pdm run bpython


.PHONY: fix
fix:
	pdm run black .
	pdm run isort .
	pdm run ruff . --fix

.PHONY: test
test:
	pdm multirun pdm run pytest tests
