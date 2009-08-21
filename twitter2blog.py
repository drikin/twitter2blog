#!/usr/bin/env python
# encoding: utf-8
"""
twitter2blog.py

Created by Kohichi Aoki on 2009-07-26.
Copyright (c) 2009 drikin.com. All rights reserved.
"""

import sys
import os
import datetime
import codecs
import re
import urlparse
import urllib2
import ConfigParser
import twitter
import flickrapi
import prowlpy
import tiny
from dateutil import zoneinfo, tz
from PyMT import *

# force utf-8 to workaround unicode problem
reload(sys)
sys.setdefaultencoding('utf-8')

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

ENABLE_DEBUG    = False

CONFIG_FILE     = "account.conf"
if( not os.path.isfile(CONFIG_FILE) ):
  print "Error: please setup '" + CONFIG_FILE + "' correctly!!!"
  sys.exit()
CONFIG = ConfigParser.SafeConfigParser()
CONFIG.read(CONFIG_FILE)

TWITTER_USERNAME    = CONFIG.get('Twitter', 'username')
TWITTER_PASSWORD    = CONFIG.get('Twitter', 'password')
TWITTER             = twitter.Api(username=TWITTER_USERNAME, password=TWITTER_PASSWORD)

MT_API_URL          = CONFIG.get('Blog',  'api_url')
MT_USERNAME         = CONFIG.get('Blog',  'username')
MT_PASSWORD         = CONFIG.get('Blog',  'password')
BLOG_ID             = CONFIG.get('Blog',  'blog_id')
MT                  = PyMT(MT_API_URL, MT_USERNAME, MT_PASSWORD)

PROWL_API_KEY       = CONFIG.get('Prowl',   'api_key')
PROWL               = prowlpy.Prowl(PROWL_API_KEY)

DATETIME_FORMAT     = '%a %b %d %H:%M:%S +0000 %Y'
TIMESTAMP_FORMAT    = '%H:%M:%S'
TIMEDELTA           = -7

LOG_DIR             = "log"
SINCE_ID_FILENAME   = LOG_DIR + "/since_id.log"
DRAFT_FILENAME      = LOG_DIR + "/entry.txt"

SHORT_FLICKR_URL    = "http://flic.kr/p/"
FLICKR_URL          = "http://www.flickr.com/photos/"
FLICKR_API_KEY      = '9f8e09d2dabc6ed826473d43a7ffecf0'
FLICKR              = flickrapi.FlickrAPI(FLICKR_API_KEY)

BASE_TAG            = "<p class='tweet'>%s</p>"
IMG_TAG             = "<a href='%s'><img src='%s' /></a><br/>" 
LINK_TAG            = "<a href='%s'>%s</a>"
TWITTER_ID_TAG      = "<a href='http://twitter.com/%s'>%s</a>"
TIME_TAG            = " <small><font color='gray'>%s</font></small>"

START_KEYWORD       = "^S\s"
END_KEYWORD         = "^E\s"
EXCLUDE_KEYWORD     = "^@\S*"
  
def b58decode(s):
  alphabet = '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
  num = len(s)
  decoded = 0 ;
  multi = 1;
  for i in reversed(range(0, num)):
    decoded = decoded + multi * ( alphabet.index( s[i] ) )
    multi = multi * len(alphabet)
  return decoded;

def bitlydecode(s):
  bitly_base = u'http://bit.ly/'
  if( s.find(bitly_base) == 0 ):
    conn = urllib2.urlopen(s)
    decoded_url = conn.geturl()
    if( decoded_url ):
      return decoded_url
    else:
      return s
  else:
    return s
  
def extractUrl(data):
  all_url =re.findall( "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", data )
  if( all_url ):
    return all_url[0]
    
def extractKeyword(data, keyword):
  results = re.findall(keyword, data)
  if( results ):
    return True
  else:
    return False
  
def convertTwitterID2Link(data):
  results = re.findall( "@[a-zA-Z0-9_]+", data )
  for result in results:
    tag = TWITTER_ID_TAG % (result[1:], result)
    data = re.sub(result, tag, data)
  return data
  
def postBlog(file_path):
  if( not (MT_API_URL and MT_USERNAME and MT_PASSWORD and BLOG_ID) ):
    return
  if( os.path.isfile(file_path) ):    
    f = codecs.open(file_path, 'r', 'utf-8')
    lines = f.readlines()
    title = lines[0]
    title = re.sub(START_KEYWORD, "", title)
    description = "".join(lines[1:])
    description = re.sub(END_KEYWORD, "", description)
    if( ENABLE_DEBUG ):
      print title
      print description
    f.close()
    
    publish = 0 # no
    content = {'title': title,
                 'description': description,
                 'categories':['twitter'] # a list of categoryID's.  List the primary category first.
                }
    if( not ENABLE_DEBUG ): 
      MT.newPost(BLOG_ID, content, publish)
    os.remove(file_path)
   
def writeLog(data, filename):
  log_file = filename
  f = codecs.open(log_file, 'a', 'utf-8')
  f.write(data)
  f.close()
  
def writeStatuses(statues):
  if( os.path.isfile(DRAFT_FILENAME) ):   
    isLogging = True
  else:
    isLogging   = False
  isPost = False
  for status in reversed(statues):
    #  get each properties from status
    created_at = datetime.datetime.strptime(status.created_at, DATETIME_FORMAT ) + datetime.timedelta(hours=TIMEDELTA)
    created_date = created_at.date()
    text = status.text
    
    # create formatted status string
    extract_url = extractUrl(text)
    image_tag = ''
    if( extract_url ):
      extract_url = tiny.decode(extract_url)
      extract_url = bitlydecode(extract_url)
      
    if( isLogging == True and extractKeyword(text, EXCLUDE_KEYWORD) ):
      continue
    
    if( isLogging == False and extractKeyword(text, START_KEYWORD) ):
      writeLog(text + '\n', DRAFT_FILENAME)
      isLogging = True
      continue
      
    if( isLogging ):
      if( extractKeyword(text, END_KEYWORD) ):
        isLogging = False
        text = re.sub(END_KEYWORD, "", text)
        isPost = True
        
      # create formatted status string
      extract_url = extractUrl(text)
      image_tag = ''
      if( extract_url ):
        original_url = extract_url
        extract_url = tiny.decode(extract_url)
        extract_url = bitlydecode(extract_url)
        # find Flickr URL
        if( extract_url.find(SHORT_FLICKR_URL) == 0 or extract_url.find(FLICKR_URL) == 0 ):
          if ( extract_url.find(SHORT_FLICKR_URL) == 0 ):
            photo_id = b58decode(extract_url[len(SHORT_FLICKR_URL):])
          else:
            path = urlparse.urlparse(extract_url)[2]          
            photo_id = path.split(u'/')[-1]
          photo_info = FLICKR.photos_getSizes(photo_id=photo_id)
          photo = photo_info.find('sizes').findall('size')[3] # medium
          photo_url = photo.attrib['url']
          photo_source = photo.attrib['source']
          # create IMG tag to flickr
          image_tag = IMG_TAG % (photo_url, photo_source)
          # remove flickr url
          url_pos = text.find(SHORT_FLICKR_URL)
          text = re.sub(original_url, "", text)
        else:
          image_tag = ''
          link_tag = LINK_TAG % (extract_url, extract_url)
          text = re.sub(extract_url, link_tag, text)
      # generate HTML
      #timestamp_tag = TIME_TAG % created_at.strftime(TIMESTAMP_FORMAT)
      timestamp_tag = ""
      output_text = image_tag + text + ' ' + timestamp_tag + '\n'
      output_text = BASE_TAG % output_text
      output_text = convertTwitterID2Link(output_text)
      writeLog(output_text, DRAFT_FILENAME)
      if( isPost ):
        # post Blog
        postBlog(DRAFT_FILENAME)
        sendNotification('Blog updated!!')
        isPost = False

def getLastID():
  if( os.path.isfile(SINCE_ID_FILENAME) ):    
    f = open(SINCE_ID_FILENAME, 'r')
    last_id = f.read()
    f.close()
    return last_id
  else:
    return 0

def writeLastID(since_id):
  f = open(SINCE_ID_FILENAME, 'w')
  if( not ENABLE_DEBUG ):
    f.write(since_id)
  f.close()
  
def sendNotification(message):
  if( not PROWL_API_KEY ):
    return
  try:
    PROWL.add('Twitter2Blog', 'Post Succeeded', message)
  except Exception,msg:
    pass

def main():
  # create working directory
  if( not os.path.isdir(LOG_DIR) ):
    os.mkdir(LOG_DIR)
  
  since_id = getLastID()
  if( ENABLE_DEBUG ):
    since_id = 0
  #statuses = TWITTER.GetUserTimeline('drikin', since_id=since_id, count=50)
  statuses = TWITTER.GetUserTimeline('drikin', since_id=since_id)
  if( statuses ):
    writeStatuses(statuses)
    writeLastID(str(statuses[0].id))

if __name__ == '__main__':
  main()
