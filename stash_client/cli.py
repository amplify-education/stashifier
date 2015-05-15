"""
Command-line interface to the stash client functions.
"""
import logging
import os
from ConfigParser import SafeConfigParser

from . import rest
from .rest import UserError, ResponseError


def get_cmd_arguments():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-o", "--organization", "-p", "--project", action="store", dest="org",
                        help=("Github organization or Stash project to query for repositories to clone."
                              "  Either this or -u is required."))
    parser.add_argument("-u", "--user", action="store", dest="user",
                        help="User to query for repositories to clone.  Either this or -o is required.")
    parser.add_argument("-U", "--override_user", action="store", dest="user_override",
                        help=("Override the local user for accessing stash.  "
                              "If not specified, local user will be used."))
    parser.add_argument("--page-size", action="store", dest="page_size", type=int,
                        help="Page size for paged responses")
    parser.add_argument("-C", "--create", action="store_true", dest="create",
                        help="Create a repository.")
    parser.add_argument("-l", "--list-repos", action="store_true", dest="list_repos",
                        help="List repositories available.")
    parser.add_argument("-perm", "--list-user-permissions", action="store_true", dest="list_user_permissions",
                        help="List the permissions for the users of this project")
    parser.add_argument("-prs", "--list-pull-requests", action="store_true", dest="list_pull_requests",
                        help="List open pull requests for this project")
    parser.add_argument("-D", action="store_true", dest="delete",
                        help="Delete a repository.")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", help="Log INFO to STDOUT")
    parser.add_argument("-r", "--repo_name", action="store", dest="repo_name",
                        help="The name of the repository.")
    parser.add_argument('positional_args', nargs='*')
    return parser.parse_args()


def main():
    try:
        _main()
    except KeyboardInterrupt:
        pass
    except UserError as oops:
        print "Input error: %s" % str(oops)
    except ResponseError as fail:
        print "Response unhappy: %s" % str(fail)
        print fail.get_response_errors()


def _main():
    from .models import StashRepo
    logging.basicConfig()
    args = get_cmd_arguments()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    # silly approach that avoids hard-coding the stash repo
    config = SafeConfigParser()
    config.read(os.path.join(os.environ["HOME"], ".stashclientcfg"))
    rest.set_host(config.get('server', 'hostname'))

    if args.delete:
        repo_name = get_repo_name(args)
        rest.set_creds(args)
        resp = rest.delete_repository(repo_name, user=args.user, project=args.org)
        if resp.text:
            print "Deletion OK: %s" % resp.json().get('message')
        else:
            print "Deletion attempt succeeded with status %d: %s" % (resp.status_code, resp.reason)
    elif args.create:
        create_repo_name = get_repo_name(args)
        rest.set_creds(args)
        resp = rest.create_repository(create_repo_name, user=args.user, project=args.org)
        repo = StashRepo(resp.json())
        print "Successfully created repo %s with clone URL %s" % (repo.name, repo.get_clone_url('ssh'))
    elif args.list_user_permissions:
        filter_on = None
        if args.positional_args:
            filter_on = args.positional_args[0]
        rest.set_creds(args)
        rest.list_user_permissions(project=args.org, filter_on=filter_on)
    elif args.list_repos:
        rest.set_creds(args)
        repo_list = rest.list_repositories(project=args.org, user=args.user, limit=args.page_size)
        print "Retrieved %d repos in %d pages" % (repo_list.entity_count, repo_list.page_count)
        for repo in repo_list.entities:
            print repo.name
    elif args.list_pull_requests:
        rest.set_creds(args)
        pr_list = rest.list_pull_requests(project=args.org, user=args.user, repository=args.repo_name)
        for pr in pr_list.entities:
            print pr._dump()
    else:
        print "No operation specified."


def get_repo_name(args):
    if not args.repo_name and not args.positional_args:
        raise UserError("Repository name must be specified either with -r or as an additional argument")
    elif args.repo_name:
        return args.repo_name
    else:
        return args.positional_args[0]


if '__main__' == __name__:
    main()
