stash_client
============

Stash client library for Amplify utilities.

To use (trivially): 

* mkvirtualenv stashclient -r requirements.pip
* ./setup.py develop
* python -mstashclient.rest -u mystashuser mynewreponame

You will also need to create a config file in ~/.stashclientcfg that looks like

    [server]
    hostname=stash.example.com
