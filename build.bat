rd /s /q i2cylib.egg-info
rd /s /q build
move /y dist\* history\
python setup.py build sdist bdist_wheel
