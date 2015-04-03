stash_client
============

Stash client library for Amplify utilities.

To use (trivially): 

* mkvirtualenv stashclient -r requirements.pip
* ./setup.py develop
* python -mstashclient.rest -u mystashuser --create -r mynewreponame

You will also need to create a config file in ~/.stashclientcfg that looks like

    [server]
    hostname=stash.example.com
    
If your stash user is different from your local user, you can override it by:

* python -mstashclient.rest -o myorganization -U myremotestashuser --create -r mynewreponame
