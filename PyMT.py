# PyMT.py version 1.0
# 
# (c) 2003 Jesse Lawrence <lawrence_jesse@yahoo.ca>

"""
 PyMT is a simple module which allows one to interface with
 the popular weblogging system, Movable Type.  MT provides 
 xml-rpc access to most of it's key functionality.  PyMT is 
 basically just a wrapper which allows you to forget about 
 the xml-rpc aspect.

 To create a new instance of PyMT, simply do the following:

      from PyMT import *
      mt = PyMT("http://yourdomain.com/cgi-bin/mt/mt-xmlrpc.cgi", "username", "password")

 PyMT METHODS:

   supportedMethods()
       - returns a list of the methods supported by Movable Type

   getRecentPosts(blogID, num_posts)

   getPost(postID)

   getUserInfo()
 
   getUsersBlogs()

   newPost(blogID, content, publish)
       - content is a dictionary with the following form:
              content = {'title':'My Title',
                         'description':'This is the body of my blog',
                         'categories':[10, 8, 3] # a list of categoryID's.  List the primary category first.
                        }
       - publish is boolean, 1 for yes, 0 for no.
       - returns the postID on success

   getPostCategories(postID)

   setPostCategories(postID)

   deletePost(postID, publish)

   editPost(postID, content, publish)
        - returns boolean true on success

   getCategoryList(blogID)

   getTrackbackPings(postID)

   publishPost(postID)
       - returns true on success, fault on failure
"""

__author__ = "Jesse Lawrence (lawrence_jesse@yahoo.ca)"
__version__ = "$Revision: 1.0 $"
__date__ = "$Date: 2003/02/19 $"
__copyright__ = "Copyright (c) 2003 Jesse Lawrence"
__license__ = "Python"



import xmlrpclib

class PyMT:
    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password

    def supportedMethods(self):
        server = xmlrpclib.Server(self.url)
        return server.mt.supportedMethods()

    def getRecentPosts(self, blogID, num_posts):
        server = xmlrpclib.Server(self.url)
        return server.metaWeblog.getRecentPosts(blogID, self.user, 
                                                self.password, num_posts)

    def getPost(self, postID):
        server = xmlrpclib.Server(self.url)
        return server.metaWeblog.getPost(postID, self.user, self.password)
        
    def getUserInfo(self):
        server = xmlrpclib.Server(self.url)
        return server.blogger.getUserInfo('', self.user, self.password)

    def getUsersBlogs(self):
        server = xmlrpclib.Server(self.url)
        return server.blogger.getUsersBlogs('', self.user, self.password)

    def newPost(self, blogID, content, publish):
        blogcontent = {'title':content['title'], 'description':content['description']}
        i = 0
        categories = []
        for n in content['categories']:
            if i == 0:
                categories.append({'categoryId':n, 'isPrimary':1})
            else:
                categories.append({'categoryId':n, 'isPrimary':0})
            i += 1
           
        server = xmlrpclib.Server(self.url)  
        blogpost = server.metaWeblog.newPost(blogID, self.user, self.password, blogcontent, 0)
        self.setPostCategories(blogpost, categories)
        if publish != 0:
            self.publishPost(blogpost)
        return blogpost
       
    def getPostCategories(self, postID):
        server = xmlrpclib.Server(self.url)
        return server.mt.getPostCategories(postID, self.user, self.password)

    def setPostCategories(self, postID, categories):
        server = xmlrpclib.Server(self.url)
        return server.mt.setPostCategories(postID, self.user, self.password,
                                           categories)
    
    def editPost(self, postID, content, publish):
        blogcontent = {'title':content['title'], 'description':content['description']}
        i = 0
        categories = []
        for n in content['categories']:
            if i == 0:
                categories.append({'categoryId':n, 'isPrimary':1})
            else:
                categories.append({'categoryId':n, 'isPrimary':0})
            i += 1                   
        server = xmlrpclib.Server(self.url)
        blogpost = server.metaWeblog.editPost(postID, self.user, self.password,
                                              content, 0)
        self.setPostCategories(postID, categories)
        if publish != 0:
            self.publishPost(postID)
        return blogpost

    def deletePost(self, postID, publish):
        server = xmlrpclib.Server(self.url)
        return server.blogger.deletePost('', postID, self.user, 
                                         self.password, publish)

    def getCategoryList(self, blogID):
        server = xmlrpclib.Server(self.url)
        return server.mt.getCategoryList(blogID, self.user, self.password)

    def getTrackbackPings(self, postID):
        server = xmlrpclib.Server(self.url)
        return server.mt.getTrackbackPings(postID)

    def publishPost(self, postID):
        server = xmlrpclib.Server(self.url)
        return server.mt.publishPost(postID, self.user, self.password)

if __name__ == "__main__":
    try:
        import pydoc
        pydoc.help("PyMT")
    except ImportError:
        print __doc__
