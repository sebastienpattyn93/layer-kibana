all: apt_prereqs lint unit_test


.PHONY: clean
clean:
	@rm -rf .tox

.PHONY: apt_prereqs
apt_prereqs:
	@# Need tox, but don't install the apt version unless we have to (don't want to conflict with pip)
	@which tox >/dev/null || (sudo apt-get install -y python3-pip && sudo -H pip3 install tox)
	@which flake8 >/dev/null || (sudo apt-get install -y python3-pip && sudo -H pip3 install flake8)

.PHONY: lint
lint_prereqs:
	@tox --notest
	@PATH=`pwd`/.tox/py34/bin:`pwd`/.tox/py35/bin flake8 $(wildcard reactive tests)
	@charm proof

.PHONY: unit_test
unit_test: apt_prereqs
	@echo Starting tests...
	tox
