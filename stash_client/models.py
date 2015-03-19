"""
Local models for Stash JSON entities, with such logic and methods as seem appropriate
to help us conceal the details of that JSON representation from the rest of the code.
"""
import json


class PagedApiPage(object):
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
        self.values = response_data['values']
        if entity_class:
            self.entities = [entity_class(el) for el in self.values]
        else:
            self.entities = None
        self.is_last_page = response_data['isLastPage']
        if not self.is_last_page:
            self.next_page_start = response_data['nextPageStart']


class StashRepo(object):
    """
    A repository object, exposing everything if you're curious enough to dig through the upstream
    response data, and just the things we care about if you're not.
    """
    def __init__(self, response_data):
        self._response_data = response_data
        self.id = response_data['id']
        self.slug = response_data['slug']
        self.name = response_data['name']

    def get_clone_url(self, protocol="ssh"):
        for clone_link in self._response_data['links']['clone']:
            if protocol == clone_link['name']:
                return clone_link['href']
        raise Exception("No clone link for protocol %s was found in project %s" % (protocol, self.name))

    def _dump(self):
        return json.dumps(self._response_data)
