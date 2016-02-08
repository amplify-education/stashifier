"""
Utility functions for directly interacting with local git repositories, as needed.
"""
## Copyright 2015 Amplify Education, Inc.

## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at

##     http://www.apache.org/licenses/LICENSE-2.0

## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

from subprocess import Popen, PIPE, STDOUT
import re


_URL_SEARCH_STRING = (
    r'(?:(?P<protocol>ssh|git)://)?'    # leading (optional) protocol information
    r'(?:(?P<ssh_user>\w+)@)?'          # (optional) ssh user
    r'(?P<host>[.\w]*?)(?::\d+/|[:/])'  # host name, trailing port (if applicable), and next separator
    r'(?:(?:~(?P<user>[^/]+)|(?P<project>[^/]+))/)?'  # stash user (~someone) or project (non-tilde cases)
    r'(?P<repo>[^/]+?)(?:\.git)?$'  # and finally, the repository name, optionally including a trailing ".git"
)


# Shamelessly ripped off from a different project, for general utility purposes
def _backtick(*args):
    """
    Run a command and return its output (STDERR and STDOUT).  Raises an exception if the
    command does not exit normally.
    """
    cmd = args[0] if isinstance(type(args[0]), list) else args
    prog = Popen(cmd, stdout=PIPE, stderr=STDOUT)
    # communicate() reads all output then wait()s for the process to exit -- wait() alone can deadlock
    (outdata, _) = prog.communicate()
    retval = prog.returncode
    if retval is None:
        raise Exception("invoked program appears not to have exited, which is theoretically impossible")
    elif retval:
        raise Exception("External program invocation %s failed: %s" % (cmd, outdata))
    return outdata


def get_remote_url(remote="origin"):
    "Get the URL for a remote (presumably 'origin') from the local git repository."
    return _backtick('git', 'config', '--get', "remote.%s.url" % remote).strip()


def get_current_branch():
    "Read the current branch from the local git repository."
    return _backtick('git', 'rev-parse', '--abbrev-ref', 'HEAD').strip()


def get_project_repo(remote="origin"):
    """
    Extract information about the project/user and remote repository from the local git config.
    """
    url = get_remote_url(remote)
    url_pattern = re.compile(_URL_SEARCH_STRING)
    match = re.match(url_pattern, url)
    return match.groupdict() if match else None
