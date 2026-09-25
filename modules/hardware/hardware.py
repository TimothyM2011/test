"""
modules/hardware/hardware.py

Data sources:
  - psutil for CPU, RAM, disk, net, battery (cheap)
  - pynvml (lazy import) for Nvidia GPU utilisation / VRAM
  - Optional: LibreHardwareMonitor for CPU/GPU temps later

Notes:
  - cpu_percent(interval=None) is non-blocking. The first call after
    process start returns 0.0; we prime it once at import.
  - disk_usage("/") on Windows maps to the current drive, which is not
    always C:. We resolve the system drive explicitly.
"""
import os
import psutil

# Prime the CPU counter so the first real reading isn't 0.0
psutil.cpu_percent(interval=None)

_gpu_handle = None
_gpu_ready = False

def _try_init_gpu():
    global _gpu_handle, _gpu_ready
    if _gpu_ready:
        return
    _gpu_ready = True
    try:
        import pynvml  # type: ignore
        pynvml.nvmlInit()
        _gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    except Exception:
        _gpu_handle = None

def _system_drive() -> str:
    drive = os.environ.get("SystemDrive", "C:")
    return drive + "\\"

def read_cheap_stats() -> dict:
    mem = psutil.virtual_memory()
    battery = None
    try:
        battery = psutil.sensors_battery()
    except Exception:
        pass
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_used_gb": round(mem.used / (1024 ** 3), 1),
        "ram_total_gb": round(mem.total / (1024 ** 3), 1),
        "ram_percent": mem.percent,
        "battery_percent": battery.percent if battery else None,
        "battery_plugged": battery.power_plugged if battery else None,
    }

def read_full_stats() -> dict:
    stats = read_cheap_stats()

    net = psutil.net_io_counters()
    stats["net_sent"] = net.bytes_sent
    stats["net_recv"] = net.bytes_recv

    try:
        disk = psutil.disk_usage(_system_drive())
        stats["disk_percent"] = disk.percent
    except Exception:
        stats["disk_percent"] = None

    _try_init_gpu()
    if _gpu_handle is not None:
        try:
            import pynvml  # type: ignore
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
