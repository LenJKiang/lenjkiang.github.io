"""Loopback-only preview with optional GitHub project-site base path."""
import argparse, functools, http.server, urllib.parse
from pathlib import Path
from common import ROOT, base_path
class Handler(http.server.SimpleHTTPRequestHandler):
 base='/'
 def translate_path(self,path):
  parsed=urllib.parse.urlsplit(path);p=parsed.path
  if not p.startswith(self.base):return str(ROOT/'workspace/working/__not_served__')
  return super().translate_path(p[len(self.base)-1:])
 def guess_type(self,path):
  if urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get('download')==['1'] and str(path).lower().endswith('.pdf'):
   return 'application/octet-stream'
  return super().guess_type(path)
 def end_headers(self):
  parsed=urllib.parse.urlsplit(self.path)
  if urllib.parse.parse_qs(parsed.query).get('download')==['1'] and parsed.path.lower().endswith('.pdf'):
   name=Path(urllib.parse.unquote(parsed.path)).name
   self.send_header('Content-Disposition','attachment; filename="'+name+'"')
  super().end_headers()
 def log_message(self,format,*args):pass
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8000);p.add_argument('--base-path',default='/');p.add_argument('--local-resources',action='store_true');a=p.parse_args();Handler.base=base_path(a.base_path)
 directory=ROOT/'dist'
 if a.local_resources:
  from build_local_preview import build_preview
  directory=build_preview()
 handler=functools.partial(Handler,directory=str(directory));server=http.server.ThreadingHTTPServer(('127.0.0.1',a.port),handler)
 print(f'Preview only: http://127.0.0.1:{a.port}{Handler.base}',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:server.server_close()
