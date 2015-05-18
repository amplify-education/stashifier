"""
REST client for Stash.
"""
import requests.api
import json
import logging
import os

from .models import PagedApiPage, PagedApiResponse, StashRepo, StashPullRequest, StashError

# for now, set at runtime from the config file (probably shouldn't be a constant anyway)
STASH_HOST = None

STASH_API_VERSION = '1.0'

_PROJECT_NAMESPACE = 'projects'
_USER_NAMESPACE = 'users'
_GROUP_NAMESPACE = 'groups'
_REPOSITORY_NAMESPACE = 'repos'
_PERMISSIONS = 'permissions'
_PULL_REQUESTS = 'pull-requests'


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
            return [StashError(error_json) for error_json in self.response.json()['errors']]
        except Exception as e:
            logging.debug("Failed to read errors from Stash response: %s", str(e))
            logging.debug("Response text was [%s]", self.response.text)
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


def _request(method, user=None, project=None, repository=None, api_path=None,
             request_body=None, query_params=None):
    api_url = create_url(user=user, project=project, repository=repository, api_path=api_path)
    resp = requests.api.request(method, api_url,
                                auth=(USERNAME, PASSWORD),
                                data=request_body,
                                params=query_params,
                                headers={'Content-type': 'application/json'}
                                )
    if not resp.ok:
        logging.debug("%s request for %s failed with response body %s", method, api_url, resp.text)
        raise ResponseError(resp)
    return resp


def _send_json_body(method, user=None, project=None, repository=None, api_path=None, post_data=None):
    if post_data is None:
        raise Exception("Message body data is not actually allowed to be None")
    json_string = json.dumps(post_data)
    logging.debug("%s of %s to %s", method.upper(), json_string, api_path)
    return _request(method, user, project, repository, api_path, request_body=json_string)


def post_json(user=None, project=None, repository=None, api_path=None, post_data=None):
    return _send_json_body('post', user, project, repository, api_path, post_data)


def put_json(user=None, project=None, repository=None, api_path=None, post_data=None):
    return _send_json_body('put', user, project, repository, api_path, post_data)


def get(user=None, project=None, repository=None, api_path=None, query_params=None):
    logging.debug("Sending GET query params %s to %s", query_params, api_path)
    return _request('get', user, project, repository, api_path, query_params=query_params)


def get_paged(user=None, project=None, repository=None, api_path=None, query_params=None,
              entity_class=None, limit=None, start=None):
    response_pages = []
    request_params = {}
    if query_params:
        request_params.update(query_params)

    if start:
        request_params['start'] = start
    elif 'start' in request_params:
        del request_params['start']

    if limit:
        logging.debug("Using page size limit of %d", limit)
        request_params['limit'] = limit
    elif 'limit' in request_params:
        del request_params['limit']

    while True:
        resp = get(user=user, project=project, repository=repository,
                   query_params=request_params, api_path=api_path)
        new_page = PagedApiPage(resp.json(), entity_class)
        response_pages.append(new_page)
        if new_page.is_last_page:
            break
        else:
            request_params['start'] = new_page.next_page_start
    return PagedApiResponse(response_pages)


def create_repository(repository_name, user=None, project=None):
    if(repository_name is None):
        raise UserError("You must specify a repository")
    if user is None and project is None:
        raise UserError("new repository needs a project or a user")
    post_data = {'name': repository_name}
    return post_json(post_data=post_data, user=user, project=project, api_path=[_REPOSITORY_NAMESPACE])


def list_repositories(user=None, project=None, limit=None):
    if user is None and project is None:
        raise UserError("Repository list needs a project or a user")
    return get_paged(user, project, api_path=[_REPOSITORY_NAMESPACE], entity_class=StashRepo, limit=limit)


def list_pull_requests(user=None, project=None, repository=None, state=None):
    if user is None and project is None:
        raise UserError("Pull request list needs a project or a user")
    if repository is None:
        raise UserError("Pull request list needs a repository name")
    query_params = {}
    # valid params: "direction" (incoming/outgoing), "at" (fully-qualified branch name), "state", "order",
    # "withAttributes" (basically count open tasks), "withProperties" (not clear this actually does anything)
    if state is not None:
        query_params['state'] = state
    return get_paged(user, project, repository, api_path=[_PULL_REQUESTS], query_params=query_params,
                     entity_class=StashPullRequest)


def create_pull_request(pr_data, user=None, project=None, repository=None):
    """The hackiest hack that ever hacked"""
    # possible attributes of a 409 response errors, for future reference:
    # option 1:
    # "context": "reviewers",
    # "exceptionName": "com.atlassian.stash.pull.InvalidPullRequestReviewersException",
    # reviewerErrors : [context=username, message=message, exceptionName=null],
    # validReviewers : [user={user_object}]
    # option 2
    #  context: null
    # "exceptionName": "com.atlassian.stash.pull.DuplicatePullRequestException",
    # "existingPullRequest": {pr_object}
    return post_json(user, project, repository, api_path=[_PULL_REQUESTS], post_data=pr_data)


def list_user_permissions(user=None, project=None, filter_on=None):
    return list_permissions(_USER_NAMESPACE, user=user, project=project, filter_on=filter_on)


def list_group_permissions(user=None, project=None, filter_on=None):
    return list_permissions(_GROUP_NAMESPACE, user=user, project=project, filter_on=filter_on)


def list_permissions(grantee_type, user=None, project=None, filter_on=None):
    if project is None:
        raise UserError("Listing project permissions needs a project")
    post_data = {'filter': filter_on} if filter_on else None
    resp = get(query_params=post_data, user=user, project=project, api_path=[_PERMISSIONS, grantee_type])
    if resp.text:
        values = resp.json()["values"]
        for value in values:
            # not hackish at all....
            if "user" in value:
                display_name = value["user"]["displayName"]
            else:
                display_name = value["group"]["name"]
            print "%s : %s" % (display_name, value["permission"])
    else:
        print "List users attempt failed with status %d: %s" % (resp.status_code, resp.reason)


def delete_repository(repository_name, user=None, project=None):
    if(repository_name is None):
        raise UserError("You must specify a repository")
    if user is None and project is None:
        raise UserError("deleting a repository needs a project or a user")
    api_url = create_url(user=user, project=project, repository=repository_name)
    resp = requests.api.delete(api_url, auth=(USERNAME, PASSWORD))
    if not resp.ok:
        raise ResponseError(resp)
    return resp
