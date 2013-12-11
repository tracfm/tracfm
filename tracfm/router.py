from urllib import quote_plus
from urllib2 import urlopen
from urlparse import urlparse, parse_qs
from django.conf import settings

# monkey patch rapidsms_httprouter to use POST instead GET
def fetch_url(url, params):
    # not yo?  just go fetch the URL
    if params.get('backend', 'tracfm_push') == 'tracfm_push':
        response = urlopen(url, timeout=15)        
        return response

    # parse our url to get our query string out
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # first try posting to our primary URL
    try:
        # first try posting to our primary URL
        url = settings.YO_PRIMARY_URL + "?" + parsed.query
        print("YO URL: " + url)
        response = urlopen(url)

        # if that worked, hurry, return the code
        if response.getcode() == 200:
            body = response.read()
            print("YO: " + body)

            # if they said this was ok, return so
            if body.find('OK') >= 0:
                return response

    except Exception as e:
        print "Got error: %s" % str(e)

        # an error is ok, we'll try our secondary URL
        pass

    # next try the secondary url
    url = settings.YO_SECONDARY_URL + "?" + parsed.query
    print("SECONDARY URL: " + url)
    response = urlopen(url)

    # read the body
    body = response.read()
    print("YO (RETRY): " + body)

    # if they said this was ok, return so
    if body.find('OK') >= 0:
        return response

    raise Exception("Got invalid body: %s" % body)
    
    

