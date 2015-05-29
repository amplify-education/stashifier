stash_client
============

Stash client library for Amplify utilities.

Using the stash client
----------------------

To use (trivially):


* mkvirtualenv stashclient -r requirements.pip
* ./setup.py develop
* stash_client -u <mystashuser> --create -r <mynewreponame>

You will also need to create a config file in ~/.stashclientcfg that looks like

    [server]
    hostname=stash.example.com
    
If your stash user is different from your local user, you can override it by:

    stash_client -o <myorganization> -U <myremotestashuser> --create -r <mynewreponame>

To see other options, just

    stash_client -h


Creating pull requests
---------------------------

To list available pull requests (for a user - use -p for a project):

    stash_client -r <mynewreponame> -u <mystashuser> 
    
Creating a new pull request can be by:

    stash_client --pull-request -r <mynewreponame> --from-branch <mybranchname> -u <mystashuser>
    
Replace -u <mystashuser> with -p <mystashproject> if it isn't a personal repo.

Alternatively, you can have the program guess your arguments based on local settings (the repo, branch, 
project and user currently in local):

    stash_client --pull-request --pr-here

Add:
    --pr-reviewers <stashusername1>,<stashusername2>, ... <stashusernameX> 

to automatically add reviewers to the pull request.  Note that you need to have the branch created in 
the remote repository before you can create a pull request.


Developing the stash client
---------------------------

Please remember to run

    rake lint

before pushing!
