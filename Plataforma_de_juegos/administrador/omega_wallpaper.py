import json
import os
import re
import subprocess
import time
from pathlib import Path

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

CACHE = {"at": 0.0, "items": [], "exe": None}
CACHE_TTL = 30


def _steam_root():
    if os.name != "nt":
        return None
    try:
        import winreg

        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for key_path in (
                r"Software\Valve\Steam",
                r"Software\WOW6432Node\Valve\Steam",
            ):
                try:
                    with winreg.OpenKey(hive, key_path) as key:
                        value, _ = winreg.QueryValueEx(key, "SteamPath")
                        if value:
                            return Path(value)
                except OSError:
                    pass
    except Exception:
        pass
    return Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Steam"


def _library_roots():
    root = _steam_root()
    roots = []
    if root:
        roots.append(root)
        vdf = root / "steamapps" / "libraryfolders.vdf"
        if vdf.exists():
            try:
                text = vdf.read_text(encoding="utf-8", errors="ignore")
                for raw in re.findall(r'\"path\"\s*\"([^\"]+)\"', text):
                    roots.append(Path(raw.replace("\\\\", "\\")))
            except OSError:
                pass
    unique = []
    seen = set()
    for p in roots:
        p = Path(p)
        k = str(p).lower()
        if k not in seen and p.exists():
            seen.add(k)
            unique.append(p)
    return unique


def _discover():
    now = time.time()
    if now - CACHE["at"] < CACHE_TTL:
        return CACHE["items"], CACHE["exe"]

    items = []
    exe = None
    for root in _library_roots():
        candidate = root / "steamapps" / "common" / "wallpaper_engine" / "wallpaper64.exe"
        if candidate.exists() and exe is None:
            exe = str(candidate)
        workshop = root / "steamapps" / "workshop" / "content" / "431960"
        if workshop.exists():
            for folder in workshop.iterdir():
                if not folder.is_dir():
                    continue
                project = next(iter(folder.glob("project.json")), None)
                if project and project.is_file():
                    items.append({"id": folder.name, "name": folder.name, "file": str(project), "kind": "project"})
                    continue
                videos = list(folder.glob("*.mp4")) + list(folder.glob("*.webm"))
                if videos:
                    items.append({"id": folder.name, "name": folder.name, "file": str(videos[0]), "kind": "video"})
    items.sort(key=lambda x: x["name"].lower())
    CACHE.update({"at": now, "items": items, "exe": exe})
    return items, exe


@staff_member_required
def wallpaper_panel(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Solo el superusuario puede controlar Wallpaper Engine."}, status=403)
    items, exe = _discover()
    return render(request, "admin/omega_wallpaper.html", {"wallpapers": items, "engine": exe})


@staff_member_required
@require_GET
def wallpaper_list(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    items, exe = _discover()
    return JsonResponse({"engine": exe, "items": items})


@staff_member_required
@require_POST
def wallpaper_set(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    try:
        payload = json.loads(request.body or "{}")
        target = str(payload.get("file", ""))
    except (ValueError, TypeError):
        return JsonResponse({"detail": "JSON inválido."}, status=400)

    items, exe = _discover()
    allowed = {item["file"] for item in items}
    if not exe:
        return JsonResponse({"detail": "No se encontró wallpaper64.exe."}, status=503)
    if target not in allowed:
        return JsonResponse({"detail": "Wallpaper no registrado por OMEGA."}, status=403)

    try:
        subprocess.Popen([exe, "-control", "openWallpaper", "-file", target],
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    except OSError as exc:
        return JsonResponse({"detail": f"No se pudo iniciar Wallpaper Engine: {exc}"}, status=500)

    return JsonResponse({"ok": True, "file": target})
