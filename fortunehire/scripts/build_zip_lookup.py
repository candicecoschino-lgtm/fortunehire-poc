"""Build same-origin ZIP/city shards from GeoNames' CC BY 4.0 postal data."""
import io,json,re,zipfile,urllib.request
from collections import defaultdict
from pathlib import Path
from datetime import datetime,timezone

SOURCE='https://download.geonames.org/export/zip/US.zip'
ROOT=Path(__file__).resolve().parents[1]
def build():
 from collect_jobs import STATES
 request=urllib.request.Request(SOURCE,headers={'User-Agent':'FortuneHire-location-data/1.0 (+https://fortunehire.netlify.app/)'})
 with urllib.request.urlopen(request,timeout=60) as response:raw=response.read(5000000)
 with zipfile.ZipFile(io.BytesIO(raw)) as archive:lines=archive.read('US.txt').decode('utf-8').splitlines()
 shards=defaultdict(dict)
 for line in lines:
  fields=line.split('\t')
  if len(fields)<5 or fields[0]!='US':continue
  code,city,state=fields[1],fields[2].strip(),fields[4]
  if not re.fullmatch(r'\d{5}',code) or not city or state not in STATES:continue
  places=shards[code[:2]].setdefault(code,[])
  if [city,state] not in places:places.append([city,state])
 target=ROOT/'public/data/zip';target.mkdir(parents=True,exist_ok=True)
 for prefix,places in sorted(shards.items()):
  (target/(prefix+'.json')).write_text(json.dumps({'schemaVersion':1,'prefix':prefix,'places':places},ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 metadata={'schemaVersion':1,'source':SOURCE,'attribution':'GeoNames','attributionUrl':'https://www.geonames.org/','license':'CC BY 4.0','licenseUrl':'https://creativecommons.org/licenses/by/4.0/','builtAt':datetime.now(timezone.utc).isoformat(),'coverage':'50 U.S. states and District of Columbia; postal-city matching, not exact job ZIP or radius.','zipCount':sum(len(p) for p in shards.values()),'shardCount':len(shards)}
 (ROOT/'public/data/zip-source.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
 (ROOT/'public/us-geography.js').write_text('export const STATE_NAMES='+json.dumps(STATES,separators=(',',':'))+';\nexport const US_STATES=Object.values(STATE_NAMES);\n',encoding='utf-8')
 print(json.dumps(metadata))
if __name__=='__main__':build()
