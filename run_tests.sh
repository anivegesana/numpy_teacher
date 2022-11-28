#!/usr/bin/env bash
python codegen
python -m coverage run -m numpy_teacher tests/*.py
python -m coverage report
python -m coverage html
