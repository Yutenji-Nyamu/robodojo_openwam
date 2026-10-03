"""Opt-in NVIDIA EGL device scope, loaded only through a private PYTHONPATH."""
import ctypes
import os

_gpu = os.environ.get('DOJO_GPU_SCOPE')
if _gpu is not None:
    if _gpu not in ('4', '5', '6', '7'):
        raise RuntimeError('DOJO_GPU_SCOPE must be a designated physical GPU')
    _libc = ctypes.CDLL(None, use_errno=True)
    if _libc.prctl(15, ctypes.c_char_p(('dojo-scope-g' + _gpu).encode()), 0, 0, 0):
        raise OSError(ctypes.get_errno(), 'Cannot set the NVIDIA app-profile name')
