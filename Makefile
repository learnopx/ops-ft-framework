all: build install test 

clean:
	rm -rf build dist *.egg-info *.pyc 

test: 
#   time -p tests/simple-topo-pingall/test.py
#   cd tests/passing-files-into-switch-container; time -p ./test.py

build: 
	python setup.py build

bdist_egg: build
	python setup.py bdist_egg
    
install: 
# some setuptools versions have a bug, need to run install
# twice to overcome caching issues
	python setup.py install
	python setup.py install

