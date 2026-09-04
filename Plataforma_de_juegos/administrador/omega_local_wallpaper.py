from __future__ import annotations

import json
import shutil
from pathlib import Path

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

WALLPAPER_DIR = Path(settings.BASE_DIR) / "administrador" / "static" / "admin" / "wallpapers"
STATE_FILE = WALLPAPER_DIR / "omega_wallpaper.json"
ALLOWED_EXTENSIONS = {".mp4", ".webm"}
MAX_SIZE = 500 * 1024 * 1024


def _is_superuser(request):
    return request.user.is_superuser


def _safe_name(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Usá un video MP4 o WEBM.")
    return suffix


def _read_state():
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, ValueError, TypeError):
        pass
    return {"file": None}


def _write_state(filename: str | None):
    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps({"file": filename}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _current_path() -> Path | None:
    state = _read_state()
    filename = state.get("file")
    if not filename:
        return None
    path = (WALLPAPER_DIR / str(filename)).resolve()
    root = WALLPAPER_DIR.resolve()
    if path.parent != root or path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return None
    return path if path.is_file() else None


def _items():
    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    current = _current_path()
    items = []
    for path in sorted(WALLPAPER_DIR.iterdir()):
        if not path.is_file() or path.name == STATE_FILE.name or path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        items.append({
            "name": path.name,
            "current": bool(current and path == current),
            "size": path.stat().st_size,
        })
    return items


@staff_member_required
def panel(request):
    if not _is_superuser(request):
        return JsonResponse({"detail": "Solo el superusuario puede controlar el wallpaper."}, status=403)
    return render(request, "admin/omega_local_wallpaper.html", {"items": _items()})


@staff_member_required
@require_GET
def listing(request):
    if not _is_superuser(request):
        return JsonResponse({"detail": "Forbidden"}, status=403)
    current = _current_path()
    return JsonResponse({
        "items": _items(),
        "current": current.name if current else None,
        "video_url": "/admin/omega/wallpapers/video/" if current else None,
    })


@staff_member_required
@require_POST
def upload(request):
    if not _is_superuser(request):
        return JsonResponse({"detail": "Forbidden"}, status=403)
    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"detail": "Seleccioná un video."}, status=400)
    if uploaded.size > MAX_SIZE:
        return JsonResponse({"detail": "El video supera 500 MB."}, status=400)
    try:
        suffix = _safe_name(uploaded.name)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    # Reemplazamos el fondo actual: un solo wallpaper activo mantiene el proyecto limpio.
    for path in WALLPAPER_DIR.iterdir():
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS:
            path.unlink(missing_ok=True)

    target = WALLPAPER_DIR / f"omega_background{suffix}"
    temp = WALLPAPER_DIR / f".omega_background{suffix}.uploading"
    try:
        with temp.open("wb") as output:
            for chunk in uploaded.chunks():
                output.write(chunk)
        temp.replace(target)
        _write_state(target.name)
    except OSError as exc:
        temp.unlink(missing_ok=True)
        return JsonResponse({"detail": f"No se pudo guardar el video: {exc}"}, status=500)

    return JsonResponse({
        "ok": True,
        "file": target.name,
        "video_url": "/admin/omega/wallpapers/video/",
        "message": "Wallpaper guardado dentro del proyecto.",
    })


@staff_member_required
@require_POST
def activate(request):
    if not _is_superuser(request):
        return JsonResponse({"detail": "Forbidden"}, status=403)
    filename = str((request.POST.get("filename") or "")).strip()
    path = (WALLPAPER_DIR / filename).resolve()
    root = WALLPAPER_DIR.resolve()
    if path.parent != root or path.suffix.lower() not in ALLOWED_EXTENSIONS or not path.is_file():
        return JsonResponse({"detail": "Wallpaper inválido."}, status=400)
    _write_state(path.name)
    return JsonResponse({"ok": True, "file": path.name, "video_url": "/admin/omega/wallpapers/video/"})


@staff_member_required
@require_POST
def delete(request):
    if not _is_superuser(request):
        return JsonResponse({"detail": "Forbidden"}, status=403)
    filename = str((request.POST.get("filename") or "")).strip()
    path = (WALLPAPER_DIR / filename).resolve()
    root = WALLPAPER_DIR.resolve()
    if path.parent != root or path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return JsonResponse({"detail": "Wallpaper inválido."}, status=400)
    if not path.is_file():
        return JsonResponse({"detail": "Ese wallpaper no existe."}, status=404)
    try:
        path.unlink()
        if _read_state().get("file") == path.name:
            _write_state(None)
    except OSError as exc:
        return JsonResponse({"detail": f"No se pudo eliminar: {exc}"}, status=500)
    return JsonResponse({"ok": True, "message": "Wallpaper eliminado del proyecto."})


@staff_member_required
@require_GET
def video(request):
    if not _is_superuser(request):
        return JsonResponse({"detail": "Forbidden"}, status=403)
    path = _current_path()
    if not path:
        return JsonResponse({"detail": "No hay wallpaper activo."}, status=404)
    content_type = "video/mp4" if path.suffix.lower() == ".mp4" else "video/webm"
    response = FileResponse(path.open("rb"), content_type=content_type)
    response["Cache-Control"] = "no-cache"
    return response
