from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

WALLPAPER_DIR = Path(settings.BASE_DIR) / "administrador" / "static" / "admin" / "wallpapers"
STATE_FILE = WALLPAPER_DIR / "omega_wallpaper.json"
ALLOWED_EXTENSIONS = {".mp4", ".webm"}
MAX_SIZE = 500 * 1024 * 1024


def _is_superuser(request):
    return bool(request.user.is_superuser)


def _safe_video_name(filename: str) -> str:
    src = Path(unquote(str(filename or "").strip()).replace("\\", "/").split("/")[-1])
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
    STATE_FILE.write_text(json.dumps({"file": filename}, ensure_ascii=False, indent=2), encoding="utf-8")


def _find_existing_name(value: object) -> str | None:
    raw = unquote(str(value or "").strip()).replace("\\", "/")
    wanted = Path(raw).name
    if not wanted:
        return None
    for item in WALLPAPER_DIR.iterdir() if WALLPAPER_DIR.exists() else ():
        if item.is_file() and item.suffix.lower() in ALLOWED_EXTENSIONS and item.name == wanted:
            return item.name
    return None


def _current_path() -> Path | None:
    name = _find_existing_name(_read_state().get("file"))
    return (WALLPAPER_DIR / name) if name else None


def _items() -> list[dict]:
    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    current = _current_path()
    return [
        {"name": p.name, "current": bool(current and p.name == current.name), "size": p.stat().st_size}
        for p in sorted(WALLPAPER_DIR.iterdir(), key=lambda p: p.name.lower())
        if p.is_file() and p.name != STATE_FILE.name and p.suffix.lower() in ALLOWED_EXTENSIONS
    ]


def _wants_json(request):
    accept = request.headers.get("Accept", "")
    return request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in accept


def _json_or_redirect(request, payload, status=200):
    if _wants_json(request):
        return JsonResponse(payload, status=status)
    return redirect("omega-wallpapers")


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
    return JsonResponse({"items": _items(), "current": current.name if current else None, "video_url": "/admin/omega/wallpapers/video/" if current else None})


@staff_member_required
@require_POST
def upload(request):
    if not _is_superuser(request):
        return JsonResponse({"detail": "Forbidden"}, status=403)
    files = request.FILES.getlist("files") or request.FILES.getlist("file")
    if not files:
        return JsonResponse({"detail": "Seleccioná uno o varios videos MP4/WEBM."}, status=400)

    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    saved, errors = [], []
    for uploaded in files:
        if uploaded.size > MAX_SIZE:
            errors.append(f"{uploaded.name}: supera 500 MB")
            continue
        try:
            filename = _safe_video_name(uploaded.name)
        except ValueError as exc:
            errors.append(f"{uploaded.name}: {exc}")
            continue
        target = WALLPAPER_DIR / filename
        i = 2
        while target.exists():
            target = WALLPAPER_DIR / f"{Path(filename).stem}_{i}{Path(filename).suffix}"
            i += 1
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

    if saved and not _current_path():
        _write_state(saved[0])
    return _json_or_redirect(request, {"ok": bool(saved), "saved": saved, "errors": errors, "message": "Videos guardados dentro del proyecto."}, 201 if saved else 400)


@staff_member_required
@require_POST
def activate(request):
    if not _is_superuser(request):
        return JsonResponse({"detail": "Forbidden"}, status=403)
    requested = request.POST.get("filename") or ""
    name = _find_existing_name(requested)
    if not name:
        try:
            name = _safe_video_name(requested)
        except ValueError as exc:
            return JsonResponse({"detail": str(exc)}, status=400)
    path = WALLPAPER_DIR / name
    if not path.is_file():
        return JsonResponse({"detail": "Wallpaper inválido."}, status=400)
    _write_state(name)
    return _json_or_redirect(request, {"ok": True, "file": name, "video_url": "/admin/omega/wallpapers/video/", "message": "Wallpaper activo."})


@staff_member_required
@require_POST
def delete(request):
    if not _is_superuser(request):
        return JsonResponse({"detail": "Forbidden"}, status=403)
    name = _find_existing_name(request.POST.get("filename") or "")
    if not name:
        return JsonResponse({"detail": "Wallpaper inválido."}, status=400)
    path = WALLPAPER_DIR / name
    try:
        was_current = bool(_current_path() and _current_path().name == name)
        path.unlink()
        if was_current:
            remaining = [item["name"] for item in _items() if item["name"] != name]
            _write_state(remaining[0] if remaining else None)
    except OSError as exc:
        return JsonResponse({"detail": f"No se pudo eliminar: {exc}"}, status=500)
    return _json_or_redirect(request, {"ok": True, "message": "Wallpaper eliminado del proyecto."})


@staff_member_required
@require_GET
def video(request):
    if not _is_superuser(request):
        return JsonResponse({"detail": "Forbidden"}, status=403)
    path = _current_path()
    if not path:
        return JsonResponse({"detail": "No hay wallpaper activo."}, status=404)
    response = FileResponse(path.open("rb"), content_type="video/mp4" if path.suffix.lower() == ".mp4" else "video/webm")
    response["Cache-Control"] = "no-cache"
    response["Accept-Ranges"] = "bytes"
    return response
