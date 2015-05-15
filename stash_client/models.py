"""
Local models for Stash JSON entities, with such logic and methods as seem appropriate
to help us conceal the details of that JSON representation from the rest of the code.
"""
import json
from datetime import datetime


class StashEntity(object):
    """
    Parent class for all Stash response entities.
    """
    def __init__(self, response_data):
        self._response_data = response_data

    def _get(self, key):
        return self._response_data.get(key)

    def _dump(self):
        return json.dumps(self._response_data)


class PagedApiResponse(object):
    """
    Container for multiple PagedApiPage objects.
    """
    def __init__(self, pages):
        self._pages = pages
        self.page_count = len(pages)
        self.entities = []
        self.values = []
        for page in pages:
            self.values.extend(page.values)
            if page.entities:
                self.entities.extend(page.entities)
        self.entity_count = len(self.values)


class PagedApiPage(StashEntity):
    """
    Paged responses take this format, according to the Stash API docs:

    {
        "size": 3,
        "limit": 3,
        "isLastPage": false,
        "values": [
            { /* result 0 */ },
            { /* result 1 */ },
            { /* result 2 */ }
        ],
        "start": 0,
        "filter": null,
        "nextPageStart": 3
    }
    """

    def __init__(self, response_data, entity_class=None):
        super(PagedApiPage, self).__init__(response_data)
        self.values = response_data['values']
        if entity_class:
            self.entities = [entity_class(el) for el in self.values]
        else:
            self.entities = None
        self.is_last_page = response_data['isLastPage']
        if not self.is_last_page:
            self.next_page_start = response_data['nextPageStart']


class StashIdentifiedEntity(StashEntity):
    """
    Base class for entities with an id, a slug and a name (project, user, and repo)
    """
    def __init__(self, response_data, entity_id=None, slug=None, name=None):
        super(StashIdentifiedEntity, self).__init__(response_data)
        self.id = entity_id or self._get("id")
        self.slug = slug or self._get("slug")
        self.name = name or self._get("name")


class StashUser(StashIdentifiedEntity):
    """
    User information from Stash.

    Available fields: display_name, email.
    Not available (yet?): type, links, active
    """
    def __init__(self, *args, **kwargs):
        super(StashUser, self).__init__(*args, **kwargs)
        self.display_name = self._get("displayName")
        self.email = self._get("emailAddress")


class StashProject(StashIdentifiedEntity):
    """
    A project (which is admittedly a pretty boring object).

    No distinguishing characteristics from a User, other than not being (necessarily) a user.
    Can actually be a user, under some circumstances...
    """
    def __init__(self, *args, **kwargs):
        super(StashProject, self).__init__(*args, **kwargs)


class StashRepo(StashIdentifiedEntity):
    """
    A repository object, exposing everything if you're curious enough to dig through the upstream
    response data, and just the things we care about if you're not.
    """
    def __init__(self, *args, **kwargs):
        super(StashRepo, self).__init__(*args, **kwargs)

    def get_clone_url(self, protocol="ssh"):
        for clone_link in self._response_data['links']['clone']:
            if protocol == clone_link['name']:
                return clone_link['href']
        raise Exception("No clone link for protocol %s was found in project %s" % (protocol, self.name))


class StashPullRequest(StashEntity):
    """
    A pull request, exposing whatever fields it seems useful to expose,
    and hopefully actually at some point also exposing enough mojo to
    actually get posted back to the server.
    """
    def __init__(self, response_data):
        super(StashPullRequest, self).__init__(response_data)
        self.id = self._get("id")
        self.state = self._get("state")
        self.title = self._get("title")
        # force floating-point division to get millisecond precision
        self.created = datetime.fromtimestamp(self._get("createdDate") / 1000.00)
        self.updated = datetime.fromtimestamp(self._get("updatedDate") / 1000.00)
        self.author = StashUser(self._get("author").get("user"))
