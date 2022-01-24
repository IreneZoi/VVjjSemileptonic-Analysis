#!/bin/bash

source /cvmfs/sft.cern.ch/lcg/views/LCG_97python3/x86_64-centos7-gcc8-opt/setup.sh

SETUP_DIR=$(dirname "${BASH_SOURCE[0]}")
PY_VER=`python -c "import sys; print('python{0}.{1}'.format(*sys.version_info))"`

export ANALYSIS_BASE=$(dirname $(readlink -f $SETUP_DIR))
export PYTHONUSERBASE=$(readlink -f $SETUP_DIR)
export PYTHONPATH=$PYTHONUSERBASE/lib/$PY_VER/site-packages:$PYTHONPATH
export PATH=$PYTHONUSERBASE/bin:$PATH

if [[ ${1} == "--with-install" ]]; then
    pip install --user -r setup/requirements.txt
fi
