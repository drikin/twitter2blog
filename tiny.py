
"""
Module for shortening/unshortening urls using tinyurl or isgd. 

On error, encode/decode will return the input url.

USAGE:

import tiny

# MAKING SHORT URLS
tiny.encode("http://www.example.com")             #Defaults to using tinyurl
# OR
tiny.encode("http://www.example.com", "tinyurl")  #Specify tinyurl
# OR
tiny.encode("http://www.example.com", "isgd")     #Specify is.gd

# REVERSE LOOKUP
tiny.decode("http://tinyurl.com/5zdnmu")
# OR 
tiny.decode("http://is.gd/bEes")

"""


import urllib

ENCODE = {"tinyurl" : ("http://tinyurl.com/api-create.php?", "url"),
          "isgd"    : ("http://is.gd/api.php?", "longurl")}

def encode(url, service="tinyurl"):
    if (ENCODE.has_key(service)):
        shortenUrl = ENCODE[service][0] + urllib.urlencode({ENCODE[service][1] : url})
        try:
            shortened = urllib.urlopen(shortenUrl).read()
            return shortened
        except:
            print "ERROR USING", service, "returning original url", url
            return url
    else:
        print "INVALID SERVICE:", service, "TRY:", ", ".join(ENCODE.keys())
        return url
    


def decodeTinyurl(shortened):
    result = urllib.urlopen("http://preview.tinyurl.com/" + shortened.rsplit("/", 1)[1]).read()
    original = result.split('<a id="redirecturl" href="', 1)[1].split('"')[0]
    return original
    
def decodeIsgd(shortened):
    result = urllib.urlopen(shortened + "-").read()
    original = result.split('points to <a href="', 1)[1].split('"', 1)[0]
    return original

DECODE = {"tinyurl" : decodeTinyurl,
          "isgd"    : decodeIsgd}
    
def decode(url):
    service = ""
    if (url.startswith("http://tinyurl.com")):
        service = "tinyurl"
    elif (url.startswith("http://is.gd")):
        service = "isgd"
        
    if (service):
        try:
            original = DECODE[service](url)
            return original
        except:
            print "ERROR USING", service, "returning original url", url
            return url
    else:
        print "DON'T KNOW HOW TO UN-SHORTEN:", url
        return url
        
