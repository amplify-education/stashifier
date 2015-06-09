"""
Command-line interface to the stash client functions.
"""
import logging
import os
from ConfigParser import SafeConfigParser

from .rest import UserError, ResponseError, StashRestClient
from .models import StashPullRequest


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
    parser.add_argument("-H", "--host", action="store", dest="host_override",
                        help=("Set the Stash hostname.  If not specified here, the value "
                              "must be set in .stashclientcfg."))
    parser.add_argument("--page-size", action="store", dest="page_size", type=int,
                        help="Page size for paged responses")
    parser.add_argument("-C", "--create", action="store_true", dest="create",
                        help="Create a repository.")
    parser.add_argument("-F", "--fork", action="store_true", dest="fork",
                        help="Create a fork of a repository in your personal project.")
    parser.add_argument("-l", "--list-repos", action="store_true", dest="list_repos",
                        help="List repositories available.")
    parser.add_argument("-perm", "--list-user-permissions", action="store_true", dest="list_user_permissions",
                        help="List the permissions for the users of this project")
    parser.add_argument("-prs", "--list-pull-requests", action="store_true", dest="list_pull_requests",
                        help="List open pull requests for this project")
    parser.add_argument("--pr-state", action="store", dest="pull_request_state",
                        choices=["OPEN", "DECLINED", "MERGED"],
                        help="List pull requests with this state (default OPEN)")
    parser.add_argument("--pull-request", action="store_true", dest="create_pr",
                        help="Create a pull request.")
    parser.add_argument("--pr-here", action="store_true", dest="pr_guess_parameters",
                        help="Use the current project and branch for the pull request")
    parser.add_argument("--pr-reviewers", action="store", dest="pr_reviewer_names",
                        help="Comma-separated list of reviewer usernames")
    parser.add_argument("--pr-title", action="store", dest="pr_title",
                        help="Pull request title")
    parser.add_argument("--pr-description", action="store", dest="pr_description",
                        help="Pull request description (markdown content)")
    parser.add_argument("--from-branch", action="store", dest="source_branch",
                        help="Source branch for a pull request")
    parser.add_argument("--fork-owner", action="store", dest="fork_id",
                        help="Project (or user namespace) containing a fork (e.g. for a pull request")
    parser.add_argument("-D", action="store_true", dest="delete",
                        help="Delete a repository.")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", help="Log INFO to STDOUT")
    parser.add_argument("-n", "--dry-run", action="store_true", dest="dry_run",
                        help="Dry run, don't actually send requests to Stash")
    parser.add_argument("-r", "--repo_name", action="store", dest="repo_name",
                        help="The name of the repository.")
    parser.add_argument('positional_args', nargs='*')
    return parser.parse_args()


def get_client(args, config):
    server = args.host_override
    # All this elaborate if-else is because config.get() doesn't take a "default" argument
    if server is None:
        if config.has_option('server', 'hostname'):
            server = config.get('server', 'hostname')
        else:
            raise UserError("Server must be set, either via configuration file or command-line option.")
    username = args.user_override
    if username is None:
        if config.has_option('server', 'user'):
            username = config.get('server', 'user')
        else:
            username = os.environ["USER"]
    logging.debug("User %s will connect to host %s", username, server)
    return StashRestClient(server, username, dry_run=args.dry_run)


def cli_wrap(func):
    try:
        rv = func()
        if rv is None:
            rv = 0
        exit(rv)
    except KeyboardInterrupt:
        exit(127)
    except UserError as oops:
        print "Input error: %s" % str(oops)
    except ResponseError as fail:
        print "Response unhappy: %s" % str(fail)
        error_messages = fail.get_response_errors()
        if error_messages:
            print "Specific error messages from the server:"
            for error in error_messages:
                print "    " + error.message
    exit(1)


@cli_wrap
def main():
    from .models import StashRepo
    logging.basicConfig()
    args = get_cmd_arguments()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    # silly approach that avoids hard-coding the stash repo
    config = SafeConfigParser()
    config.read(os.path.join(os.environ["HOME"], ".stashclientcfg"))
    client = get_client(args, config)

    if args.delete:
        repo_name = get_repo_name(args)
        resp = client.delete_repository(repo_name, user=args.user, project=args.org)
        if resp.text:
            print "Deletion OK: %s" % resp.json().get('message')
        else:
            print "Deletion attempt succeeded with status %d: %s" % (resp.status_code, resp.reason)
    elif args.create:
        create_repo_name = get_repo_name(args)
        resp = client.create_repository(create_repo_name, user=args.user, project=args.org)
        repo = StashRepo(resp.json())
        print "Successfully created repo %s with clone URL %s" % (repo.name, repo.get_clone_url('ssh'))
    elif args.fork:
        create_repo_name = get_repo_name(args)
        resp = client.fork_repository(create_repo_name, user=args.user, project=args.org)
        repo = StashRepo(resp.json())
        print "Successfully forked repo %s with clone URL %s" % (repo.name, repo.get_clone_url('ssh'))
    elif args.list_user_permissions:
        filter_on = None
        if args.positional_args:
            filter_on = args.positional_args[0]
        client.list_user_permissions(project=args.org, filter_on=filter_on)
    elif args.list_repos:
        repo_list = client.list_repositories(project=args.org, user=args.user, limit=args.page_size)
        print "Retrieved %d repos in %d pages" % (repo_list.entity_count, repo_list.page_count)
        for repo in repo_list.entities:
            print repo.name
    elif args.list_pull_requests:
        pr_list = client.list_pull_requests(project=args.org, user=args.user, repository=args.repo_name,
                                            state=args.pull_request_state)
        for pr in pr_list.entities:
            author = pr.author
            print "'%s' (%d) created at %s by %s (%s)" % (pr.title, pr.id, pr.created,
                                                          author.display_name, author.email)
            if pr.is_local():
                print "    local merge from source branch %s into %s" % (
                    pr.source.display_id, pr.destination.display_id)
            else:
                print "    merge from remote fork %s, branch %s into local branch %s" % (
                    pr.source.repository.project.name, pr.source.display_id, pr.destination.display_id)
            if pr.reviewers:
                print "    Reviewers: %s" % ", ".join([who.display_name for who in pr.reviewers])
            if pr.approved_by:
                print "    Approved by: %s" % ", ".join([who.display_name for who in pr.approved_by])
            if args.verbose:
                print pr._dump()
    elif args.create_pr:
        reviewer_names = []
        if args.pr_reviewer_names:
            reviewer_names = [name.strip() for name in args.pr_reviewer_names.split(",")]
        if args.pr_guess_parameters:
            # guess based on local git repository information
            from .local_git import get_project_repo, get_current_branch
            guesses = get_project_repo()
            user, project, repo = (guesses[k] for k in ['user', 'project', 'repo'])
            source_branch = get_current_branch()
        # command-line args take priority:
        if args.org or args.user:  # only one should end up set
            user = args.user
            project = args.org
        if args.repo_name:
            repo = args.repo_name
        if args.source_branch:
            source_branch = args.source_branch
        pr_data = StashPullRequest.postable_pull_request(
            repository=repo,
            fork_owner=args.fork_id,
            source_branch=source_branch,
            description=args.pr_description,
            title=args.pr_title,
            reviewers=reviewer_names
        )
        if args.dry_run:
            print pr_data, user, project, repo
            return
        pr_resp = client.create_pull_request(user=user, project=project, repository=repo, pr_data=pr_data)
        created_pr = StashPullRequest(pr_resp.json())
        print "Created pull request '%s' (#%d) at %s" % (created_pr.title, created_pr.id, created_pr.created)
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
