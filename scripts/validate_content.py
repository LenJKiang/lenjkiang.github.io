import sys
from common import validate
if __name__=='__main__':
 try:
  d=validate(); print(f"PASS content: {len(d['publications'])} publications, {len(d['courses'])} courses, {len(d['resources'])} approved assets")
 except (AssertionError,ValueError,KeyError,TypeError) as e: print('FAIL content:',e); sys.exit(1)
