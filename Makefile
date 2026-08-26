.PHONY: install run test check

install:
	python3 -m pip install -e '.[test]'

run:
	python3 -m data_agent_network_demo --open

test:
	python3 -m pytest

check: test
	python3 -m compileall -q prompits-lite phemacast-lite demos/data-agent-network-demo
