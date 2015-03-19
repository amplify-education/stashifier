#!/bin/bash
#
# This script performs a deploy of the component into 
# the QA environment, then runs integration tests.
#
# It is intended to be run on the Jenkins server,
# but can be run locally as well.
#
export PATH=/opt/wgen-3p/python27/bin:$PATH
export PATH=/opt/wgen-3p/ruby-1.9/bin:$PATH
export WORKSPACE=${WORKSPACE:-$PWD}
export PIP_LOG=${PIP_LOG:-$WORKSPACE/pip.log}
rake virtualenv:create
source venv/bin/activate
rake jenkins:deploy_and_test
