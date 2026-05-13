import tracemalloc
import threading
import gc
import time

from pynetdicom import AE, AllStoragePresentationContexts, debug_logger, evt
from pynetdicom.sop_class import Verification

debug_logger()


def handle(event):
    assoc = event.assoc
    ae = assoc.ae
    # print(ae._servers)

    # for assoc in ae._servers[0].active_associations:
    #     print(assoc)

    for thread in threading.enumerate():
        print(f"  {thread.name}")

    print()


tracemalloc.start(10)

ae = AE()
ae.network_timeout = 5
ae.acse_timeout = 5
ae.dimse_timeout = 5
ae.supported_contexts = AllStoragePresentationContexts
ae.add_supported_context(Verification)

# AE's UIDs -> 632 in PCs + 1 (implementation class name)

if False:
    ae.start_server(
        ("localhost", 11112),
        evt_handlers=[(evt.EVT_CONN_OPEN, handle)],
    )

if True:
    try:
        ae.start_server(
            ("localhost", 11112),
            evt_handlers=[
                (evt.EVT_CONN_OPEN, handle),
            ],
        )
    except Exception as exc:
        print(exc)

    print(threading.enumerate())
    # time.sleep(5)
    # gc.collect()
    snapshot = tracemalloc.take_snapshot()
    stats = snapshot.statistics("lineno")

    for s in stats[:20]:
        print(s)
