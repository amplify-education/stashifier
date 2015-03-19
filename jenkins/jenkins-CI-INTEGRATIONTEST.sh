#!/bin/bash
#
# This script performs an integration test of the component,
# deploying the component into the CI environment,
# creating a virtualenv, installing test dependencies,
# running the functional and integration tests,
# then (if those pass) copying the RPM to the QA repository.
#
# It is intended to be run on the Jenkins server,
# but can be run locally as well.
#
export PATH=/opt/wgen-3p/python27/bin:$PATH
export PATH=/opt/wgen-3p/ruby-1.9/bin:$PATH
export WORKSPACE=${WORKSPACE:-$PWD}
export PIP_LOG=${PIP_LOG:-$WORKSPACE/pip.log}
export QA_REPO=${QA_REPO:-/tmp}
rake virtualenv:create
source venv/bin/activate
rake jenkins:ci_integrationtest
