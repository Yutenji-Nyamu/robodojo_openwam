"""Backport only OpenWAM-Official/OpenWAM PR 37; no model or config changes."""
import ast,hashlib,logging,os
from collections import OrderedDict
from pathlib import Path
from typing import Any

ORIGINAL_SHA='4d78462a5affd7d8e1022517a6ebd6d543fcb518dbfd2c40e14bc02aab4f07fa'
ENGINE_REL='XPolicyLab/policy/OpenWAM/OpenWAM/openwam/deploy/engine.py'
OLD='            evicted_key, _ = self.popitem(last=False)\n'
NEW=('            # Upstream PR 37: bypass __getitem__ recency changes during eviction.\n'
     '            evicted_key = next(iter(self))\n'
     '            super().__delitem__(evicted_key)\n')

def cache_class(source):
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='_BoundedPromptEmbedCache')
    namespace={'OrderedDict':OrderedDict,'Any':Any,'logger':logging.getLogger('repair.cache'),'DEFAULT_PROMPT_EMBED_CACHE_MAXSIZE':32}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'exact-live-cache-class','exec'),namespace)
    return namespace[node.name]

def prepare_cache_fix(path,archive=None,apply=False):
    path=Path(path);raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==ORIGINAL_SHA
    source=raw.decode();assert source.count(OLD)==1
    original=cache_class(source)(maxsize=3)
    reproduced=False
    try:
        for key in ['probe','a','b','c']:original[key]=key
    except KeyError:reproduced=True
    assert reproduced, 'Expected live-cache failure was not reproduced'
    fixed=source.replace(OLD,NEW)
    cache=cache_class(fixed)(maxsize=3)
    for key in ['probe','a','b','c']:cache[key]=key
    assert list(cache)==['a','b','c']
    assert cache['a']=='a'
    cache['d']='d';assert list(cache)==['c','a','d']
    cache['e']='e';assert list(cache)==['a','d','e']
    for i in range(100):cache[str(i)]=i;assert cache[str(i)]==i and len(cache)==3
    report={'upstream':'https://github.com/OpenWAM-Official/OpenWAM/pull/37',
            'upstream_merge':'f6d9f1059eb63a8a76dc60e07da2dad21615a161','path':str(path),
            'before_sha256':ORIGINAL_SHA,'after_sha256':hashlib.sha256(fixed.encode()).hexdigest(),
            'original_keyerror_reproduced':True,'fixed_lru_checks_passed':True,'applied':apply}
    if apply:
        archive=Path(archive);archive.mkdir(parents=True,exist_ok=True)
        with (archive/'engine-original.py').open('xb') as f:f.write(raw)
        with (archive/'engine-fixed.py').open('xb') as f:f.write(fixed.encode())
        temp=path.with_name(path.name+'.repair-20260929-ssh-v1')
        with temp.open('x') as f:f.write(fixed);f.flush();os.fsync(f.fileno())
        temp.chmod(path.stat().st_mode & 0o777)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==ORIGINAL_SHA
        os.replace(temp,path)
    return report
