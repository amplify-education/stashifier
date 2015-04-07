stash_client
============

Stash client library for Amplify utilities.

Using the stash client
----------------------

To use (trivially):


* mkvirtualenv stashclient -r requirements.pip
* ./setup.py develop
* stash_client -u mystashuser --create -r mynewreponame

You will also need to create a config file in ~/.stashclientcfg that looks like

    [server]
    hostname=stash.example.com
    
If your stash user is different from your local user, you can override it by:

    stash_client -o myorganization -U myremotestashuser --create -r mynewreponame

To see other options, just

    stash_client -h

Developing the stash client
---------------------------

This would be better if we had a section on automatically creating
pull requests, but we can't create pull requests yet.  Guess we need
somebody to do a pull request for that?  D'oh!

However, please remember to run

    rake lint

before pushing!
