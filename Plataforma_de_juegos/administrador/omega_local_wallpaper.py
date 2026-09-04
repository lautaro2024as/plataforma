from __future__ import annotations

import json
import re
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
    return bool(request.user.is_superuser)


def _safe_video_name(filename: str) -> str:
    src = Path(filename)
    suffix = src.suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Solo se permiten videos MP4 o WEBM.")
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", src.stem).strip("._-") or "wallpaper"
    return stem + suffix


def _read_state() -> dict:
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"file": None}
    except (OSError, ValueError, TypeError):
        return {"file": None}


def _write_state(filename: str | None) -> None:
    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps({"file": filename}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _safe_path(filename: str) -> Path | None:
    raw = str(filename or "").strip()
    if not raw:
        return None
    path = (WALLPAPER_DIR / raw).resolve()
    root = WALLPAPER_DIR.resolve()
    if path.parent != root or path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return None
    return path


def _current_path() -> Path | None:
    state = _read_state()
    path = _safe_path(str(state.get("file") or ""))
    return path if path and path.is_file() else None


def _items() -> list[dict]:
    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    current = _current_path()
    items = []
    for path in sorted(WALLPAPER_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_file() or path.name == STATE_FILE.name or path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        items.append({
            "name": path.name,
            "current": bool(current and path.resolve() == current.resolve()),
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

    uploads = request.FILES.getlist("files") or request.FILES.getlist("file")
    if not uploads:
        return JsonResponse({"detail": "Seleccioná uno o varios videos MP4/WEBM."}, status=400)

    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    saved = []
    errors = []

    for uploaded in uploads:
        if uploaded.size > MAX_SIZE:
            errors.append(f"{uploaded.name}: supera 500 MB")
            continue
        try:
            filename = _safe_video_name(uploaded.name)
        except ValueError as exc:
            errors.append(f"{uploaded.name}: {exc}")
            continue

        target = WALLPAPER_DIR / filename
        if target.exists():
            index = 2
            while (WALLPAPER_DIR / f"{Path(filename).stem}_{index}{Path(filename).suffix}").exists():
                index += 1
            target = WALLPAPER_DIR / f"{Path(filename).stem}_{index}{Path(filename).suffix}"

        temp = WALLPAPER_DIR / f".{target.name}.uploading"
        try:
            with temp.open("wb") as output:
                for chunk in uploaded.chunks():
                    output.write(chunk)
            temp.replace(target)
            saved.append(target.name)
        except OSError as exc:
            temp.unlink(missing_ok=True)
            errors.append(f"{uploaded.name}: {exc}")

    # Si no había fondo activo y guardamos al menos uno, activa el primero automáticamente.
    if saved and not _current_path():
        _write_state(saved[0])

    payload = {"ok": bool(saved), "saved": saved, "errors": errors, "message": "Videos guardados dentro del proyecto."}
    return JsonResponse(payload, status=201 if saved else 400)


@staff_member_required
@require_POST
def activate(request):
    if not _is_superuser(request):
        return JsonResponse({"detail": "Forbidden"}, status=403)
    filename = str(request.POST.get("filename") or "").strip()
    path = _safe_path(filename)
    if not path or not path.is_file():
        return JsonResponse({"detail": "Wallpaper inválido."}, status=400)
    _write_state(path.name)
    return JsonResponse({"ok": True, "file": path.name, "video_url": "/admin/omega/wallpapers/video/"})


@staff_member_required
@require_POST
def delete(request):
    if not _is_superuser(request):
        return JsonResponse({"detail": "Forbidden"}, status=403)
    filename = str(request.POST.get("filename") or "").strip()
    path = _safe_path(filename)
    if not path:
        return JsonResponse({"detail": "Wallpaper inválido."}, status=400)
    if not path.is_file():
        return JsonResponse({"detail": "Ese wallpaper no existe."}, status=404)
    try:
        was_current = _current_path() and _current_path().name == path.name
        path.unlink()
        remaining = [item for item in _items() if item["name"] != path.name]
        if was_current:
            _write_state(remaining[0]["name"] if remaining else None)
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
    response["Accept-Ranges"] = "bytes"
    return response
