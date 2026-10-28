import os
from build_site import build
from common import ROOT, load
if __name__=='__main__':
 owner,repo=os.environ['REPOSITORY'].split('/')
 base='/' if repo.lower()==owner.lower()+'.github.io' else '/'+repo+'/'
 cfg=load(ROOT/'config/site.yml')
 origin=os.environ.get('SITE_ORIGIN') or cfg.get('canonical_origin') or 'https://'+owner+'.github.io'
 build(base,origin)
