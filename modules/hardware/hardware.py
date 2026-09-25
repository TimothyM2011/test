"""
modules/hardware/hardware.py

Efficiency rules followed here:
  - psutil for everything it can give us (CPU, RAM, disk, net, battery)
    since it's far cheaper than WMI per-call.
  - GPU (pynvml) is imported lazily, only on first use, and only if
    this module is actually enabled - so users without an Nvidia GPU
    or who disable this module pay zero cost for it.
  - cpu_percent() uses non-blocking mode (no interval sleep) - we
    call it every tick and let the tick interval itself be the
    sampling window.
"""

import psutil

_gpu_handle = None
_gpu_init_attempted = False


def _try_init_gpu():
    global _gpu_handle, _gpu_init_attempted
    if _gpu_init_attempted:
        return
    _gpu_init_attempted = True
    try:
        import pynvml
        pynvml.nvmlInit()
        _gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    except Exception:
        _gpu_handle = None


def read_cheap_stats() -> dict:
    """Used in COLLAPSED tier - cheapest possible read."""
    mem = psutil.virtual_memory()
    battery = psutil.sensors_battery()
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_used_gb": round(mem.used / (1024 ** 3), 1),
        "ram_total_gb": round(mem.total / (1024 ** 3), 1),
        "ram_percent": mem.percent,
        "battery_percent": battery.percent if battery else None,
    }


def read_full_stats() -> dict:
    """Used in EXPANDED tier - includes GPU/disk/network."""
    stats = read_cheap_stats()

    net = psutil.net_io_counters()
    stats["net_sent"] = net.bytes_sent
    stats["net_recv"] = net.bytes_recv

    try:
        disk = psutil.disk_usage("/")
        stats["disk_percent"] = disk.percent
    except Exception:
        stats["disk_percent"] = None

    _try_init_gpu()
    if _gpu_handle is not None:
        try:
            import pynvml
            util = pynvml.nvmlDeviceGetUtilizationRates(_gpu_handle)
            mem = pynvml.nvmlDeviceGetMemoryInfo(_gpu_handle)
            stats["gpu_percent"] = util.gpu
            stats["vram_used_gb"] = round(mem.used / (1024 ** 3), 1)
            stats["vram_total_gb"] = round(mem.total / (1024 ** 3), 1)
        except Exception:
            stats["gpu_percent"] = None
    else:
        stats["gpu_percent"] = None

    return stats
