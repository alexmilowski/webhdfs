import requests
import logging
from requests.auth import HTTPBasicAuth
import sys

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def verbose_log(function):
   def wrapper(self,*args,**kwargs):
      r = function(self,*args,**kwargs)
      if self.verbose:
         logger = logging.getLogger(__name__)
         for key in r.request.headers:
            value = r.request.headers[key]
            logger.debug('{}: {}'.format(key,value))

      return r
   return wrapper


class Client:

   def __init__(self,service='',base=None,secure=False,host='localhost',port=50070,gateway=None,username=None,password=None):
      self.service = service
      self.base = base
      if self.base is not None and self.base[-1]!='/':
         self.base = self.base + '/'
      self.secure = secure
      self.host = host if host is not None else 'localhost'
      self.port = port if port is not None else 50070
      self.gateway = gateway
      self.username = username
      self.password = password
      self.proxies = None
      self.verify = True
      self.verbose = False

   def enable_verbose(self):
      self.verbose = True;
      # These two lines enable debugging at httplib level (requests->urllib3->http.client)
      # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
      # The only thing missing will be the response.body which is not logged.
      try:
         import http.client as http_client
      except ImportError:
         # Python 2
         import httplib as http_client
      #http_client.HTTPConnection.debuglevel = 1

      # You must initialize logging, otherwise you'll not see debug output.
      logging.basicConfig()
      logging.getLogger().setLevel(logging.DEBUG)
      requests_log = logging.getLogger("requests.packages.urllib3")
      requests_log.setLevel(logging.DEBUG)
      requests_log.propagate = True


   def service_url(self,version='v1'):
      if self.base is not None:
         if self.gateway is None:
            return '{}{}/{}'.format(self.base,self.service,version)
         else:
            return '{}gateway/{}/{}/{}'.format(self.base,self.gateway,self.service,version)
      protocol = 'https' if self.secure else 'http'
      if self.gateway is None:
         return '{}://{}:{}/{}/{}'.format(protocol,self.host,self.port,self.service,version)
      else:
         return '{}://{}:{}/gateway/{}/{}/{}'.format(protocol,self.host,self.port,self.gateway,self.service,version)

   def auth(self):
      return HTTPBasicAuth(self.username,self.password) if self.username is not None else None

   @verbose_log
   def post(self,url,params={},data=None,headers=None):
      return requests.post(
         url,
         params=params,
         auth=self.auth(),
         data=data,
         headers=headers,
         proxies=self.proxies,
         verify=self.verify)

   @verbose_log
   def put(self,url,params={},data=None,headers=None,allow_redirects=True):
      return requests.put(
         url,
         params=params,
         auth=self.auth(),
         data=data,
         headers=headers,
         allow_redirects=allow_redirects,
         proxies=self.proxies,
         verify=self.verify)

   @verbose_log
   def get(self,url,params={},allow_redirects=True):
      return requests.get(
         url,
         params=params,
         auth=self.auth(),
         allow_redirects=allow_redirects,
         proxies=self.proxies,
         verify=self.verify)

   @verbose_log
   def delete(self,url,params={}):
      return requests.delete(
         url,
         params=params,
         auth=self.auth(),
         proxies=self.proxies,
         verify=self.verify)

   def _exception(self,status,message):
      error = None;
      if status==401:
         error = PermissionError(message)
      else:
         error = IOError(message)
      error.status = status
      return error;
