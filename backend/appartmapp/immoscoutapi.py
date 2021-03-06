import urllib
import oauth2 as oauth
import json

def sanitize_is24(item):
    result = item['resultlist.realEstate']['address']
    result['description'] = item['resultlist.realEstate'].get('title')
    #import pdb; pdb.set_trace()
    if 'titlePicture' in item['resultlist.realEstate']:
        result['image_url'] = item['resultlist.realEstate']['titlePicture']['urls'][0]['url'][1]['@href']
    else:
        result['image_url'] = ''
    #import pdb; pdb.set_trace()
    result['information'] = item['realEstateId']
    return result

class ImmoScout24Api(object):
    def __init__(self, auth, domain='http://sandbox.immobilienscout24.de', headers=None):
        """
        auth must be a dictionary with the following keys:
        consumer_key, consumer_secret, access_token, access_secret
        """
        consumer = oauth.Consumer(auth['consumer_key'], auth['consumer_secret'])
        token = oauth.Token(auth['access_token'], auth['access_secret'])
        self.headers = {'Accept': 'application/json'}
        if headers is not None:
            self.headers.update(headers)
        self.client = oauth.Client(consumer, token)
        self.domain = domain

    def make_get_request(self, url):
        response = self.client.request(url, headers=self.headers, body=None)
        if response[0]['status'] != '200':
            raise Exception(response)
        try:
            return json.loads(response[1])
        except ValueError:
            raise Exception(response[1])

    def build_url(self, path, **kwargs):
        return "%s%s?%s" % (self.domain, path, urllib.urlencode(kwargs))

    def get(self, path, path_args=None, **kwargs):
        if path_args:
            path = path % path_args
        url = self.build_url(path, **kwargs)
        return self.make_get_request(url)

    def search_iterator(self, func, *args, **kwargs):
        res = func(*args, **kwargs)
        yield res
        while True:
            if not 'paging' in res['resultlist.resultlist']:
                raise StopIteration
            paging = res['resultlist.resultlist']['paging']
            if paging['pageNumber'] == paging['numberOfPages']:
                raise StopIteration
            url = paging['next']['@xlink.href']
            res = self.make_get_request(url)
            yield res

    def radius_search(self, realestatetype, lat, lng, radius, **kwargs):
        return self.get('/restapi/api/search/v1.0/search/radius',
            realestatetype=realestatetype,
            geocoordinates='%s;%s;%s' % (lat, lng, radius), **kwargs)

    def radius_search_list(self, realestatetype, lat, lng, radius, **kwargs):
        return self.search_iterator(self.radius_search, realestatetype, lat, lng, radius, **kwargs)

    def region_search(self, realestatetype, regions, **kwargs):
        if isinstance(regions, list) or isinstance(regions, tuple):
            regions = ','.join(regions)
        return self.get('/restapi/api/search/v1.0/search/region',
                realestatetype=realestatetype,
                geocodes=regions, **kwargs)

    def region_search_list(self, realestatetype, regions, **kwargs):
        return self.search_iterator(self.region_search, realestatetype, regions, **kwargs)

    def expose(self, exposeid):
        return self.get('/restapi/api/search/v1.0/expose/%s', (exposeid,))

    def expose_attachment_list(self, exposeid):
        return self.get('/restapi/api/search/v1.0/expose/%s/attachment', (exposeid,))

    def expose_attachment(self, exposeid, attachmentid):
        return self.get('/restapi/api/search/v1.0/expose/%s/attachment/%s', (exposeid, attachmentid))
