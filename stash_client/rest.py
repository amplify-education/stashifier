"""
REST client for Stash.
"""
import requests.api
import json
import logging
import os
from ConfigParser import SafeConfigParser

STASH_HOST = None

STASH_API_VERSION = '1.0'

BASE_URL = 'https://%s/rest/api/%s' % (STASH_HOST, STASH_API_VERSION)

_PROJECT_NAMESPACE = 'projects'
_USER_NAMESPACE = 'users'
_REPOSITORY_NAMESPACE = 'repos'
_PERMISSIONS = 'permissions'


class UserError(Exception):
    pass


class ResponseError(Exception):
    def __init__(self, response):
        self.response = response

    def __str__(self):
        return "Application failure with status code %d: %s" % (
            self.response.status_code, self.response.reason)


def set_creds(args):
    import getpass
    
    username = os.environ["USER"]
    if args.user_override:
        username = args.user_override
    password = getpass.getpass("Stash password for %s: " % username)
    global USERNAME
    global PASSWORD
    (USERNAME, PASSWORD) = (username, password)

def create_url(user=None, project=None, repository=None, api_path=None):
    if user is not None and project is not None:
        raise UserError("EITHER user or project may be supplied")
    components = ['https://%s/rest/api/%s' % (STASH_HOST, STASH_API_VERSION)]
    if user is not None:
        components.append(_USER_NAMESPACE)
        components.append(user)
    elif project is not None:
        components.append(_PROJECT_NAMESPACE)
        components.append(project)
    if repository is not None:
        components.append(_REPOSITORY_NAMESPACE)
        components.append(repository)
    if api_path is not None:
        components.extend(api_path)
    return "/".join(components)


def post_json(user=None, project=None, repository=None, api_path=None, post_data=None):
    if post_data is None:
        raise Exception("POST data is not actually allowed to be None")
    api_url = create_url(user=user, project=project, repository=repository, api_path=api_path)
    json_string = json.dumps(post_data)
    logging.debug("Posting %s to %s", json_string, api_url)
    resp = requests.api.post(api_url, data=json_string, auth=(USERNAME, PASSWORD),
                             headers={'Content-type': 'application/json'})
    if not resp.ok:
        raise ResponseError(resp)
    return resp

def get_json(user=None, project=None, repository=None, api_path=None, post_data=None):
    if post_data is None:
        raise Exception("POST data is not actually allowed to be None")
    api_url = create_url(user=user, project=project, repository=repository, api_path=api_path)
    json_string = json.dumps(post_data)
    logging.debug("Posting %s to %s", json_string, api_url)
    resp = requests.api.get(api_url, data=json_string, auth=(USERNAME, PASSWORD),
                             headers={'Content-type': 'application/json'})
    if not resp.ok:
        raise ResponseError(resp)
    return resp

def create_repo(repository_name, user=None, project=None):
    if(repository_name is None):
        raise UserError("You must specify a repository")
    if user is None and project is None:
        raise UserError("new repository needs a project or a user")
    post_data = {'name': repository_name}
    return post_json(post_data=post_data, user=user, project=project, api_path=[_REPOSITORY_NAMESPACE])

def list_user_permissions( user=None, project=None, group_name=None):
    if project is None:
        raise UserError("Listing project permisisons needs a project")
    api_cmd = _PERMISSIONS + "/users"
    post_data = {'filter':group_name}
    resp = get_json(post_data=post_data, user=user, project=project, api_path=[api_cmd])
    if resp.text:
        values = resp.json()["values"]
        for value in values :
            print value["user"]["displayName"] + " : " + value["permission"]
    else:
        raise ResponseError("List users attempt failed with status %d: %s" % (resp.status_code, resp.reason))
    
def delete_repo(repository_name, user=None, project=None):
    if(repository_name is None):
        raise UserError("You must specify a repository")
    if user is None and project is None:
        raise UserError("deleting a repository needs a project or a user")
    api_url = create_url(user=user, project=project, repository=repository_name)
    resp = requests.api.delete(api_url, auth=(USERNAME, PASSWORD))
    if not resp.ok:
        raise ResponseError(resp)
    return resp

def get_cmd_arguments():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-o", "--organization", action="store", dest="org",
                        help=("Github organization or Stash project to query for repositories to clone."
                              "  Either this or -u is required."))
    parser.add_argument("-u", "--user", action="store", dest="user",
                        help="User to query for repositories to clone.  Either this or -o is required.")
    parser.add_argument("-U", "--override_user", action="store", dest="user_override",
                        help="Override the local user for accessing stash.  If not specified, local user will be used.")
    parser.add_argument("-C", "--create", action="store_true", dest="create",
                        help="Create a repo")
    parser.add_argument("-perm", "--list_user_permissions", action="store_true", dest="list_user_permissions",
                        help="List the permissions for the users of this project")
    parser.add_argument("-D", action="store_true", dest="delete",
                        help="DELETE IT.")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", help="Log INFO to STDOUT")
    parser.add_argument("-r", "--repo_name", action="store", dest="repo_name", help="The name of the repository.")
    return parser.parse_args()
    
def main():
    from .models import StashRepo
    logging.basicConfig()
    args = get_cmd_arguments()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    # silly approach that avoids hard-coding the stash repo
    config = SafeConfigParser()
    config.read(os.path.join(os.environ["HOME"], ".stashclientcfg"))
    global STASH_HOST
    STASH_HOST = config.get('server', 'hostname')

    if args.delete:
        set_creds(args)
        resp = delete_repo(args.repo_name, user=args.user, project=args.org)
        if resp.text:
            print "Deletion OK: %s" % resp.json().get('message')
        else:
            print "Deletion attempt succeeded with status %d: %s" % (resp.status_code, resp.reason)
    elif args.create:
        set_creds(args)
        resp = create_repo(args.repo_name, user=args.user, project=args.org)
        repo = StashRepo(resp.json())
        print "Successfully created repo %s with clone URL %s" % (repo.name, repo.get_clone_url('ssh'))
    elif args.list_user_permissions:
        set_creds(args)
        list_user_permissions(user=args.user, project=args.org)
    else:
        print "No operation specified."


if '__main__' == __name__:
    try:
        main()
    except KeyboardInterrupt:
        pass
    except UserError as oops:
        print "Input error: %s" % str(oops)
    except ResponseError as fail:
        print "Response unhappy: %s" % str(fail)
