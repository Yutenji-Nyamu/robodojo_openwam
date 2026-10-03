"""Bounded Vulkan device-enumeration probe; no simulation or kernels."""
import ctypes as C
import json
import os
import subprocess
import uuid
import xml.etree.ElementTree as E

gpu = int(os.environ.get('DOJO_GPU_SCOPE', '4'))
assert gpu in (4, 5, 6, 7)
assert C.CDLL(None).prctl(15, f'dojo-scope-g{gpu}'.encode(), 0, 0, 0) == 0
V, U = C.c_void_p, C.c_uint32
class App(C.Structure):
    _fields_ = [('sType', U), ('pNext', V), ('name', C.c_char_p), ('version', U), ('engine', C.c_char_p), ('engineVersion', U), ('api', U)]
class Instance(C.Structure):
    _fields_ = [('sType', U), ('pNext', V), ('flags', U), ('app', C.POINTER(App)), ('layers', U), ('layerNames', V), ('extensions', U), ('extensionNames', V)]
class IDs(C.Structure):
    _fields_ = [('sType', U), ('pNext', V), ('device', C.c_ubyte*16), ('driver', C.c_ubyte*16), ('luid', C.c_ubyte*8), ('nodeMask', U), ('valid', U)]
class Props(C.Structure):
    _fields_ = [('sType', U), ('pNext', V), ('data', C.c_ubyte*2048)]
class Queue(C.Structure):
    _fields_ = [('sType', U), ('pNext', V), ('flags', U), ('family', U), ('count', U), ('priorities', C.POINTER(C.c_float))]
class Device(C.Structure):
    _fields_ = [('sType', U), ('pNext', V), ('flags', U), ('queueCount', U), ('queues', C.POINTER(Queue)), ('layers', U), ('layerNames', V), ('extensions', U), ('extensionNames', V), ('features', V)]

vk = C.CDLL('libvulkan.so.1')
vk.vkCreateInstance.argtypes = [C.POINTER(Instance), V, C.POINTER(V)]
vk.vkEnumeratePhysicalDevices.argtypes = [V, C.POINTER(U), V]
vk.vkGetPhysicalDeviceProperties2.argtypes = [V, C.POINTER(Props)]
vk.vkCreateDevice.argtypes = [V, C.POINTER(Device), V, C.POINTER(V)]
vk.vkDestroyDevice.argtypes = [V, V]
vk.vkDestroyInstance.argtypes = [V, V]
app = App(0, None, b'dojo-scope', 0, None, 0, (1 << 22) | (1 << 12))
info = Instance(1, None, 0, C.pointer(app), 0, None, 0, None)
instance = V()
assert vk.vkCreateInstance(C.byref(info), None, C.byref(instance)) == 0
logical = V()
try:
    count = U()
    assert vk.vkEnumeratePhysicalDevices(instance, C.byref(count), None) == 0
    physical = (V * count.value)()
    assert vk.vkEnumeratePhysicalDevices(instance, C.byref(count), physical) == 0
    found = []
    for handle in physical:
        ids = IDs(); ids.sType = 1000071004
        props = Props(); props.sType = 1000059001; props.pNext = C.addressof(ids)
        vk.vkGetPhysicalDeviceProperties2(handle, C.byref(props))
        found.append(dict(uuid=str(uuid.UUID(bytes=bytes(ids.device))), name=bytes(props.data)[20:276].split(b'\0')[0].decode()))
    print(json.dumps(dict(pid=os.getpid(),devices=found)), flush=True)
    expected = subprocess.check_output(['nvidia-smi','-i',str(gpu),'--query-gpu=uuid','--format=csv,noheader'], text=True).strip().removeprefix('GPU-')
    target = [i for i, row in enumerate(found) if row['uuid'] == expected]
    assert len(target) == 1, 'Target UUID ambiguous/missing'
    priority = C.c_float(1)
    queue = Queue(2, None, 0, 0, 1, C.pointer(priority))
    device = Device(3, None, 0, 1, C.pointer(queue), 0, None, 0, None, None)
    assert vk.vkCreateDevice(physical[target[0]], C.byref(device), None, C.byref(logical)) == 0
    root = E.fromstring(subprocess.check_output(['nvidia-smi','-q','-x']))
    own = [dict(gpu=i,type=p.findtext('type'),memory=p.findtext('used_memory'))
           for i,g in enumerate(root.findall('gpu')) for p in g.findall('./processes/process_info') if p.findtext('pid') == str(os.getpid())]
    print(json.dumps(dict(target_gpu=gpu,visible_count=len(found),own_contexts=own)), flush=True)
finally:
    if logical.value: vk.vkDestroyDevice(logical, None)
    vk.vkDestroyInstance(instance, None)
