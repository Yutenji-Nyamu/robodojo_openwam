"""Stable, bounded output naming for repeated Dojo borrowing cycles."""
import hashlib
from pathlib import Path

def resumed_name(old_run, cycle):
    old=Path(old_run).name
    original=old.split('-after-dojo-',1)[0]
    # Hash the full lineage to distinguish retries without appending it forever.
    digest=hashlib.sha256((old+'\0'+str(cycle)).encode()).hexdigest()[:12]
    label=original.encode()[:100].decode(errors='ignore')
    cycle_label=Path(cycle).name.encode()[:50].decode(errors='ignore')
    result=label+'-after-dojo-'+cycle_label+'-'+digest
    assert len(result.encode())<=180 and '/' not in result
    return result
