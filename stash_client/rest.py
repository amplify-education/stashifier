"""
REST client for Stash.
"""
import requests.api
import json
import logging
import os

# for now, set at runtime from the config file (probably shouldn't be a constant anyway)
STASH_HOST = None

STASH_API_VERSION = '1.0'

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

    def get_response_errors(self):
        try:
            return self.response.json()['errors']
        except Exception as e:
            logging.debug("Failed to read errors from Stash response: %s", str(e))
            return None

def set_host(hostname):
    logging.info("Stash host will be %s", hostname)
    global STASH_HOST
    STASH_HOST = hostname


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
        logging.debug("Failure with response body %s", resp.body)
        raise ResponseError(resp)
    return resp


def get(user=None, project=None, repository=None, api_path=None, query_params=None):
    api_url = create_url(user=user, project=project, repository=repository, api_path=api_path)
    logging.debug("Sending GET query params %s to %s", query_params, api_url)
    resp = requests.api.get(api_url, params=query_params,
                            auth=(USERNAME, PASSWORD),
                            headers={'Content-type': 'application/json'})
    if not resp.ok:
        logging.debug("Failure with response body %s", resp.json())
        raise ResponseError(resp)
    return resp


def create_repo(repository_name, user=None, project=None):
    if(repository_name is None):
        raise UserError("You must specify a repository")
    if user is None and project is None:
        raise UserError("new repository needs a project or a user")
    post_data = {'name': repository_name}
    return post_json(post_data=post_data, user=user, project=project, api_path=[_REPOSITORY_NAMESPACE])


def list_user_permissions(user=None, project=None, filter_on=None):
    if project is None:
        raise UserError("Listing project permissions needs a project")
    post_data = {'filter': filter_on} if filter_on else None
    resp = get(query_params=post_data, user=user, project=project, api_path=[_PERMISSIONS, _USER_NAMESPACE])
    if resp.text:
        values = resp.json()["values"]
        for value in values:
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
