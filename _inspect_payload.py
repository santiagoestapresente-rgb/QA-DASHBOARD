import json
from pathlib import Path

d = json.loads(Path("_payload_keys.json").read_text(encoding="utf-8"))
print("COUNTRY0", d.get("by_channel0"))

# reload full overview for nested keys
import urllib.request

ov = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/api/dashboard?page=overview&channel=All&country=All&weeks=all", timeout=60).read())
meta = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/api/meta", timeout=60).read())
qa = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/api/dashboard?page=qa&channel=All&country=All&weeks=all", timeout=60).read())
cs = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/api/dashboard?page=csat&channel=All&country=All&weeks=all", timeout=60).read())
rc = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/api/dashboard?page=recontact&channel=All&country=All&weeks=all", timeout=60).read())
al = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/api/dashboard?page=alerts&channel=All&country=All&weeks=all", timeout=60).read())

o = ov["overview"]


def keys(obj, name):
    if obj is None:
        print(name, None)
        return
    if isinstance(obj, list):
        print(name, "list", len(obj), list(obj[0].keys()) if obj else None)
        if obj:
            print("  sample", {k: obj[0][k] for k in list(obj[0])[:8]})
        return
    if isinstance(obj, dict):
        print(name, "dict", list(obj.keys()))
        return
    print(name, type(obj).__name__, obj)


print("META country0", meta["countries"][:1], list(meta["countries"][0].keys()))
keys(o.get("resolution"), "resolution")
keys(o.get("aht"), "aht")
keys(o.get("crit"), "crit")
keys(o.get("subcr"), "subcr")
keys(o.get("taxonomy"), "taxonomy")
keys(o.get("supervisors"), "supervisors")
keys(o.get("csat_by_biz"), "csat_by_biz")
keys(o.get("qa_by_lob"), "qa_by_lob")
keys(o.get("weekly"), "weekly")
keys(qa.get("qa"), "qa_pack")
q = qa["qa"]
for k in q:
    keys(q[k], f"qa.{k}")
c = cs["csat"]
print("CSAT keys", list(c.keys()))
for k in c:
    keys(c[k], f"csat.{k}")
r = rc["recontact"]
print("RC keys", list(r.keys()))
for k in r:
    keys(r[k], f"rc.{k}")
a = al["alerts"]
print("AL keys", list(a.keys()))
for k in a:
    if k in {"low", "high"}:
        keys(a[k], f"al.{k}")
    else:
        print(f"al.{k}", a[k] if not isinstance(a[k], (list, dict)) else type(a[k]).__name__)
