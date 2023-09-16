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

.PHONY: setup-venvs
setup-venvs:
	PDM_MULTIRUN_USE_VENVS=0 pdm multirun pdm venv create --name \$$PDM_MULTIRUN_CURRENT \$$PDM_MULTIRUN_CURRENT

.PHONY: install
install:
	pdm multirun pdm install

.PHONY: sync
sync:
	pdm multirun pdm sync


.PHONY: test
test:
	pdm multirun pytest tests

.PHONY: fix
fix:
	pdm run black .
	pdm run isort .
	pdm run ruff . --fix

init: setup-venvs sync