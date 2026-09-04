import platform
import socket
import time

import psutil
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connection
from django.http import JsonResponse

from .models import AlertaMalware, Juego, LicenciaCompra, PerfilUsuario


def _fmt_uptime(seconds: float) -> str:
    seconds = int(max(0, seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days:
        return f"{days}d {hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _ping_db_ms() -> float | None:
    started = time.perf_counter()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return round((time.perf_counter() - started) * 1000, 1)
    except Exception:
        return None


@staff_member_required
def system_stats(request):
    partitions = psutil.disk_partitions(all=False)
    disk_mount = partitions[0].mountpoint if partitions else "/"
    cpu = psutil.cpu_percent(interval=0.08)
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage(disk_mount)
    net = psutil.net_io_counters()
    db_ms = _ping_db_ms()

    games = Juego.objects.count()
    published = Juego.objects.filter(estado="publicado").count()
    malware = AlertaMalware.objects.filter(resuelta=False).count()
    users = PerfilUsuario.objects.count()
    licenses = LicenciaCompra.objects.count()

    return JsonResponse(
        {
            "cpu": round(cpu, 1),
            "ram": round(vm.percent, 1),
            "ram_used_gb": round(vm.used / (1024**3), 1),
            "ram_total_gb": round(vm.total / (1024**3), 1),
            "disk": round(disk.percent, 1),
            "disk_used_gb": round(disk.used / (1024**3), 1),
            "disk_total_gb": round(disk.total / (1024**3), 1),
            "net_sent_mb": round(net.bytes_sent / (1024**2), 1),
            "net_recv_mb": round(net.bytes_recv / (1024**2), 1),
            "uptime": _fmt_uptime(time.time() - psutil.boot_time()),
            "os": f"{platform.system()} {platform.release()}",
            "hostname": socket.gethostname(),
            "db": "CONNECTED" if db_ms is not None else "OFFLINE",
            "db_ms": db_ms,
            "games": games,
            "published": published,
            "malware": malware,
            "users": users,
            "licenses": licenses,
        }
    )
