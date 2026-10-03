"""Inspect EGL device visibility with one short-lived initialized display."""
import ctypes as C
import json
import os
import subprocess
import xml.etree.ElementTree as E

gpu=int(os.environ.get('DOJO_GPU_SCOPE','4'))
assert C.CDLL(None).prctl(15,f'dojo-scope-g{gpu}'.encode(),0,0,0)==0
egl=C.CDLL('libEGL.so.1');V=C.c_void_p;I=C.c_int
egl.eglGetProcAddress.argtypes=[C.c_char_p];egl.eglGetProcAddress.restype=V
query=C.CFUNCTYPE(C.c_uint,I,C.POINTER(V),C.POINTER(I))(egl.eglGetProcAddress(b'eglQueryDevicesEXT'))
platform=C.CFUNCTYPE(V,C.c_uint,V,C.POINTER(I))(egl.eglGetProcAddress(b'eglGetPlatformDisplayEXT'))
device_string=C.CFUNCTYPE(C.c_char_p,V,I)(egl.eglGetProcAddress(b'eglQueryDeviceStringEXT'))
devices=(V*32)();n=I();assert query(32,devices,C.byref(n))
print(json.dumps(dict(pid=os.getpid(),egl_count=n.value,drm_devices=[str(device_string(devices[i],0x3233)) for i in range(n.value)],extensions=[str(device_string(devices[i],0x3055)) for i in range(n.value)])),flush=True)
egl.eglInitialize.argtypes=[V,C.POINTER(I),C.POINTER(I)];egl.eglTerminate.argtypes=[V]
d=platform(0x313F,devices[0],None);major=I();minor=I()
assert egl.eglInitialize(d,C.byref(major),C.byref(minor))
try:
 egl.eglBindAPI.argtypes=[C.c_uint];assert egl.eglBindAPI(0x30A2)
 egl.eglChooseConfig.argtypes=[V,C.POINTER(I),C.POINTER(V),I,C.POINTER(I)]
 config=V();num=I();attrs=(I*5)(0x3040,8,0x3033,1,0x3038)
 assert egl.eglChooseConfig(d,attrs,C.byref(config),1,C.byref(num)) and num.value
 egl.eglCreateContext.argtypes=[V,V,V,C.POINTER(I)];egl.eglCreateContext.restype=V
 ctx=egl.eglCreateContext(d,config,None,(I*1)(0x3038));assert ctx
 egl.eglMakeCurrent.argtypes=[V,V,V,V];assert egl.eglMakeCurrent(d,None,None,ctx)
 root=E.fromstring(subprocess.check_output(['nvidia-smi','-q','-x']))
 rows=[dict(gpu=i,type=p.findtext('type'),memory=p.findtext('used_memory')) for i,g in enumerate(root.findall('gpu')) for p in g.findall('./processes/process_info') if p.findtext('pid')==str(os.getpid())]
 print(json.dumps(dict(egl_version=[major.value,minor.value],own_contexts=rows)),flush=True)
finally:egl.eglTerminate(d)
