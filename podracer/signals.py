import os
import signal

from contextlib import contextmanager


@contextmanager
def forward_signals(send_signal, *forwarded):
  handler = lambda signum, _ : send_signal(signum)

  for signum in forwarded:
    signal.signal(signum, handler)

  try:
    yield
  finally:
    for signum in forwarded:
      signal.signal(signum, signal.SIG_DFL)
