# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build


# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# add a dependency, this is an alias for poetry add that also updates the requirements.txt file
add:
	@scripts/add_python_dependency $(ARGUMENTS)

# copies metadata to path included in pypet2bids project to enable packaging of those files w/ poetry
buildpackage:
	@cp pypet2bids/pyproject.toml pypet2bids/pypet2bids/pyproject.toml
	@rm -rf pypet2bids/dist
	@cd pypet2bids && poetry lock && poetry build

publish:
	@cd pypet2bids && poetry publish

installpoetry:
	@cd scripts && ./installpoetry

# installs latest package
installpackage:
	@scripts/installpackage

testphantoms:
	@scripts/testphantoms

html:
	@cd docs && make html

installdependencies:
	@cd pypet2bids; \
	python -m pip install --upgrade pip; \
	pip install poetry; \
	poetry install --with dev

collectphantoms:
ifeq (, $(wildcard ./PHANTOMS.zip))
	@wget -O PHANTOMS.zip https://openneuropet.s3.amazonaws.com/US-sourced-OpenNeuroPET-Phantoms.zip
else
	@echo "PHANTOMS.zip already exists"
endif

decompressphantoms:
	@unzip -o PHANTOMS.zip

testecatcli:
	@cd pypet2bids; \
	poetry run python -m pypet2bids.ecat_cli --help; \
	poetry run python -m pypet2bids.ecat_cli ../OpenNeuroPET-Phantoms/sourcedata/SiemensHRRT-JHU/Hoffman.v --dump

testecatread:
	@cd pypet2bids; \
	export TEST_ECAT_PATH="../OpenNeuroPET-Phantoms/sourcedata/SiemensHRRT-JHU/Hoffman.v"; \
	export READ_ECAT_SAVE_AS_MATLAB="$$PWD/tests/ECAT7_multiframe.mat"; \
	export NIBABEL_READ_ECAT_SAVE_AS_MATLAB="$$PWD/tests/ECAT7_multiframe.nibabel.mat"; \
	poetry run python3 -m tests.test_ecatread

testotherpython:
	cd pypet2bids; \
	export TEST_DICOM_IMAGE_FOLDER="../OpenNeuroPET-Phantoms/sourcedata/SiemensBiographPETMR-NIMH/AC_TOF"; \
	poetry run pytest --ignore=tests/test_write_ecat.py tests/ -vvv

pythongithubworkflow: installdependencies collectphantoms decompressphantoms testecatread testecatcli testotherpython
	@echo finished running python tests

black:
	@for file in `find pypet2bids/ -name "*.py"`; do \
		black $$file; \
	done
