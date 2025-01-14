import httplib, urllib, base64, json, sys
# This is a python script to test the CMS API.
# To use this script, edit the configuration file brightcove_oauth.txt
# with your brightcove account ID, and a client ID and client secret for
# an Oauth credential that has CMS API - Videos Read permission.
# You can find instructions on how to generate Oauth credentials
# http://docs.brightcove.com/en/video-cloud/cms-api/getting-started/quick-start-cms.html
# This script demonstrates how to refresh the access token
# in handling 401 - Unauthorized errors from the CMS API
# Because the Oauth tokens have a 300 second time to live,
# The refresh logic to handle 401 errors will be a normal part of runtime behavior.
# Note that the client_id and client_secret secure the access to the CMS API
# Therefore, it is not advisable to expose them to browsers. These are meant for
# server to server communication to obtain an access token.
# The access token can be exposed to the browser. Its limited permissions and expiry
# time make limit the duration and scope of its usage should it be observed in network
# traffic or obtained from a browser.
class AuthError(Exception):
def __init__(self):
self.msg = "auth error"
# read the oauth secrets and account ID from a configuration file
def loadSecret():
# read the s3 creds from json file
try:
        credsFile=open('brightcove_oauth.txt')
        creds = json.load(credsFile)
return creds
except Exception, e:
print "Error loading oauth secret from local file called 'brightcove_oauth.txt'"
print "\tThere should be a local file in this directory called brightcove_oauth.txt "
print "\tWhich has contents like this:"
print """

		{
        "account_id": "1234567890001",
		"client_id": "30ff0909-0909-33d3-ae88-c9887777a7b7",
		"client_secret": "mzKKjZZyeW5YgsdfBD37c5730g397agU35-Dsgeox6-73giehbeihgleh659dhgjhdegessDge0s0ynegg987t0996nQ"
		}

		"""
		sys.exit("System error: " + str(e) );
# get the oauth 2.0 token
def getAuthToken(creds):
    conn = httplib.HTTPSConnection("oauth.brightcove.com")
    url =  "/v4/access_token"
    params = {
"grant_type": "client_credentials"
    }
    client = creds["client_id"];
    client_secret = creds["client_secret"];
    authString = base64.encodestring('%s:%s' % (client, client_secret)).replace('\n', '')
    requestUrl = url + "?" + urllib.urlencode(params)
    headersMap = {
"Content-Type": "application/x-www-form-urlencoded",
"Authorization": "Basic " + authString
    };
    conn.request("POST", requestUrl, headers=headersMap)
    response = conn.getresponse()
if response.status == 200:
        data = response.read()
        result = json.loads( data )
return result["access_token"]
# call analytics api for video views in the last 30 days
def getVideoViews( token , account ):
    conn = httplib.HTTPSConnection("data.brightcove.com")
    url =  "/analytics-api/videocloud/account/" + account + "/report/"
    params = {
"dimensions": "video",
"limit": "10",
"sort": "video_view",
"fields": "video,video_name,video_view",
"format": "json"
    }
    requestUrl = url + "?" + urllib.urlencode(params)
    headersMap = {
"Authorization": "Bearer " + token
    };
    conn.request("POST", requestUrl, headers=headersMap)
    response = conn.getresponse()
if response.status == 200:
        data = response.read()
        result = json.loads( data )
return result
elif response.status == 401:
# if we get a 401 it is most likely because the token is expired.
raise AuthError
else:
raise Exception('API_CALL_ERROR' + " error " + str(response.status) )
# call CMS API to return the number of videos in the catalog
def getVideos( token , account ):
    conn = httplib.HTTPSConnection("cms.api.brightcove.com")
    url =  "/v1/accounts/" + account + "/counts/videos/"
    requestUrl = url
print "GET " + requestUrl
    headersMap = {
"Authorization": "Bearer " + token
    };
    conn.request("GET", requestUrl, headers=headersMap)
    response = conn.getresponse()
if response.status == 200:
        data = response.read()
        result = json.loads( data )
return result
elif response.status == 401:
# if we get a 401 it is most likely because the token is expired.
raise AuthError
else:
raise Exception('API_CALL_ERROR' + " error " + str(response.status) )
def demo():
    creds = loadSecret()
    token = getAuthToken(creds)
    account = creds["account"];
try:
        results = getVideos( token , account )
except AuthError, e:
# handle an auth error by re-fetching a auth token again
        token = getAuthToken(creds)
        results = getVideoViews( token , account )
# print the videos
print results
if __name__ == "__main__":
  demo();
