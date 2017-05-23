from .client import Client
from datetime import datetime
import argparse
import sys
import os

def parseAuth(value):
   if value is None or len(value)==0:
      return (None,None)
   else:
      colon = value.find(':')
      if colon<0:
         return (value,None)
      else:
         return (value[0:colon],value[colon+1:])

def main():
   parser = argparse.ArgumentParser(description="WebHDFS Client")

   parser.add_argument(
        '--base',
        nargs="?",
        help="The base URI of the service")
   parser.add_argument(
        '--host',
        nargs="?",
        default='localhost',
        help="The host of the service (may include port)")
   parser.add_argument(
        '--port',
        nargs="?",
        default=50070,
        help="The port of the service")
   parser.add_argument(
        '--secure',
        action='store_true',
        default=False,
        help="The port of the service")
   parser.add_argument(
        '--gateway',
        nargs="?",
        help="The KNOX gateway name")
   parser.add_argument(
      '--auth',
       help="The authentication for the request (colon separated username/password)")

   parser.add_argument(
      'command',
      nargs=argparse.REMAINDER,
      help='The command')
#   parser.add_argument(
#      'args',
#      nargs='*',
#      help='The command arguments')
   args = parser.parse_args()

   user = parseAuth(args.auth)
   client = Client(base=args.base,username=user[0],password=user[1]) if args.base is not None else \
            Client(secure=args.secure,host=args.host,port=args.port,gateway=args.gateway,username=user[0],password=user[1])

   try:
      if args.command[0]=='ls':
         lsparser = argparse.ArgumentParser(description="ls")
         lsparser.add_argument(
            '-b',
            action='store_true',
            dest='reportbytes',
            default=False,
            help="Report sizes in binary")
         lsparser.add_argument(
            '-l',
            action='store_true',
            dest='detailed',
            default=False,
            help="List details")
         lsparser.add_argument(
            'paths',
            nargs='*',
            help='a list of paths')
         lsargs = lsparser.parse_args(args.command[1:])

         if len(lsargs.paths)==0:
            lsargs.paths = ['/']
         for path in lsargs.paths:
            listing = client.list_directory(path)
            max = 0;
            for name in sorted(listing):
               if len(name)>max:
                  max = len(name)
            for name in sorted(listing):

               if not lsargs.detailed:
                  print(name)
                  continue

               info = listing[name]
               if name=='':
                  name = path[path.rfind('/')+1:]
                  max = len(name)
               ftype = info['type']
               size = int(info['length'])
               modtime = datetime.fromtimestamp(int(info['modificationTime'])/1e3)

               fspec = '{:'+str(max)+'}\t{}\t{}'
               fsize = '0'
               if ftype=='DIRECTORY':
                  name = name + '/'
               else:
                  if lsargs.reportbytes or size<1024:
                     fsize = str(size)+'B'
                  elif size<1048576:
                     fsize = '{:0.1f}KB'.format(size/1024)
                  elif size<1073741824:
                     fsize = '{:0.1f}MB'.format(size/1024/1024)
                  else:
                     fsize = '{:0.1f}GB'.format(size/1024/1024/1024)
               print(fspec.format(name,fsize,modtime.isoformat()))
      elif args.command[0]=='cat':
         for path in args.command[1:]:
            input = client.open(path)
            for chunk in input:
               sys.stdout.buffer.write(chunk)
      elif args.command[0]=='mkdir':
         for path in args.command[1:]:
            if not client.make_directory(path):
               sys.stderr.write('mkdir failed: {}\n'.format(path))
               sys.exit(1)

      elif args.command[0]=='mv':
         if len(args.command)!=3:
            sys.stderr.write('Invalid number of arguments: {}'.format(len(args.command)-1))
         if not client.mv(args.command[1],args.command[2]):
            sys.stderr.write('Move failed.\n')
            sys.exit(1)
      elif args.command[0]=='rm':
         rmparser = argparse.ArgumentParser(description="rm")
         rmparser.add_argument(
            '-r',
            action='store_true',
            dest='recursive',
            default=False,
            help="Recursively remove files/directories")
         rmparser.add_argument(
            'paths',
            nargs='*',
            help='a list of paths')
         rmargs = rmparser.parse_args(args.command[1:])
         for path in rmargs.paths:
            if not client.remove(path,recursive=rmargs.recursive):
               sys.stderr.write('Cannot remove: {}\n'.format(path))
               sys.exit(1)
      elif args.command[0]=='cp':
         cpparser = argparse.ArgumentParser(description="cp")
         cpparser.add_argument(
            '-f',
            action='store_true',
            dest='force',
            default=False,
            help="Force an overwrite")
         cpparser.add_argument(
            'paths',
            nargs='*',
            help='a list of paths')
         cpargs = cpparser.parse_args(args.command[1:])
         #TODO support wilecards
         if len(cpargs.paths)!=2:
            sys.stderr.write('Invalid number of arguments: {}'.format(len(cpargs.paths)))
         size = os.path.getsize(cpargs.paths[0])
         path = cpargs.paths[1]
         if path[-1]=='/':
            slash = cpargs.paths[0].rfind('/')
            if slash > 0:
               path = path + cpargs.paths[0][slash:]
            else:
               path = path + '/' + cpargs.paths[0]
         with open(cpargs.paths[0],'rb') as input:
            if not client.copy(input,path,size=size,overwrite=cpargs.force):
               sys.stderr.write('Move failed.\n')
               sys.exit(1)
      else:
         sys.stderr.write('Unknown command: '+args.command[0]+'\n')
         sys.exit(1)
   except ConnectionError as err:
      sys.stderr.write('Cannot connect to service.\n')
      sys.stderr.write(str(err)+'\n')
      sys.exit(1)
   except PermissionError as err:
      sys.stderr.write('Unauthorized\n');
      sys.exit(error.status)
   except IOError as err:
      sys.stderr.write(str(err)+'\n')
      if err.status==403:
         sys.stderr.write('Forbidden!\n')
      elif err.status==404:
         sys.stderr.write('Not found!\n')
      sys.exit(err.status)

   sys.exit(0)

if __name__ == '__main__':
   main()
