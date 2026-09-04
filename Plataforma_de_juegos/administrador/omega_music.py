from __future__ import annotations

import json
import re
from pathlib import Path

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST


# La música vive dentro del proyecto para que pueda viajar junto con él.
MUSIC_ROOT = Path(settings.BASE_DIR) / "administrador" / "static" / "admin" / "music"
META_FILE = MUSIC_ROOT / "library.json"
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac", ".webm"}
MAX_BYTES = 250 * 1024 * 1024
SAFE_NAME = re.compile(r"[^a-zA-Z0-9._ -]+")


def _ensure_root():
    MUSIC_ROOT.mkdir(parents=True, exist_ok=True)
    if not META_FILE.exists():
        META_FILE.write_text("[]", encoding="utf-8")


def _read_library():
    _ensure_root()
    try:
        data = json.loads(META_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError, TypeError):
        return []


def _write_library(items):
    _ensure_root()
    tmp = META_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(META_FILE)


def _public_item(item):
    return {"id": item["id"], "name": item["name"], "url": f"/admin/omega/music/stream/{item['id']}/", "size": item.get("size", 0)}


@staff_member_required
def music_player(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Solo el superusuario puede usar el Music Core."}, status=403)
    return render(request, "admin/omega_music_player.html")


@staff_member_required
def music_list(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Solo el superusuario puede administrar la música."}, status=403)
    return JsonResponse({"items": [_public_item(item) for item in _read_library()]})


@staff_member_required
@require_POST
def music_upload(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"detail": "No se recibió ningún archivo."}, status=400)
    if uploaded.size > MAX_BYTES:
        return JsonResponse({"detail": "El archivo supera el límite de 250 MB."}, status=400)

    original = Path(uploaded.name)
    ext = original.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return JsonResponse({"detail": "Formato no permitido. Usa MP3, WAV, OGG, M4A, AAC, FLAC o WEBM."}, status=400)

    _ensure_root()
    safe_stem = SAFE_NAME.sub("_", original.stem).strip(" .") or "audio"
    items = _read_library()
    item_id = 1
    used = {str(item.get("id")) for item in items}
    while str(item_id) in used:
        item_id += 1

    filename = f"{item_id:04d}_{safe_stem}{ext}"
    destination = MUSIC_ROOT / filename
    with destination.open("wb") as target:
        for chunk in uploaded.chunks():
            target.write(chunk)

    item = {"id": str(item_id), "name": original.name, "filename": filename, "size": uploaded.size}
    items.append(item)
    _write_library(items)
    return JsonResponse({"ok": True, "item": _public_item(item)})


def _content_type(path):
    return {".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg", ".m4a": "audio/mp4", ".aac": "audio/aac", ".flac": "audio/flac", ".webm": "audio/webm"}.get(path.suffix.lower(), "application/octet-stream")


@staff_member_required
@require_GET
def music_stream(request, music_id):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    item = next((x for x in _read_library() if str(x.get("id")) == str(music_id)), None)
    if not item:
        return JsonResponse({"detail": "Tema no encontrado."}, status=404)

    path = (MUSIC_ROOT / item.get("filename", "")).resolve()
    root = MUSIC_ROOT.resolve()
    if path.parent != root or path.suffix.lower() not in ALLOWED_EXTENSIONS or not path.is_file():
        return JsonResponse({"detail": "Archivo de música no encontrado."}, status=404)

    total = path.stat().st_size
    range_header = request.headers.get("Range", "").strip()
    if range_header.startswith("bytes="):
        spec = range_header[6:].split(",", 1)[0].strip()
        try:
            start_s, end_s = spec.split("-", 1)
            if start_s:
                start = int(start_s)
                end = int(end_s) if end_s else total - 1
            else:
                suffix_len = int(end_s)
                start = max(total - suffix_len, 0)
                end = total - 1
            if start < 0 or start >= total or end < start:
                raise ValueError
            end = min(end, total - 1)
            length = end - start + 1
            file_obj = path.open("rb")
            file_obj.seek(start)
            response = FileResponse(file_obj, content_type=_content_type(path), status=206)
            response["Content-Range"] = f"bytes {start}-{end}/{total}"
            response["Content-Length"] = str(length)
            response["Accept-Ranges"] = "bytes"
            response["Cache-Control"] = "no-cache"
            return response
        except (ValueError, OSError):
            return JsonResponse({"detail": "Rango de audio inválido."}, status=416)

    response = FileResponse(path.open("rb"), content_type=_content_type(path))
    response["Content-Length"] = str(total)
    response["Accept-Ranges"] = "bytes"
    response["Cache-Control"] = "no-cache"
    return response


@staff_member_required
@require_POST
def music_delete(request, music_id):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    items = _read_library()
    item = next((x for x in items if str(x.get("id")) == str(music_id)), None)
    if not item:
        return JsonResponse({"detail": "Tema no encontrado."}, status=404)
    path = (MUSIC_ROOT / item.get("filename", "")).resolve()
    root = MUSIC_ROOT.resolve()
    try:
        if path.parent == root and path.exists():
            path.unlink()
    except OSError:
        pass
    _write_library([x for x in items if str(x.get("id")) != str(music_id)])
    return JsonResponse({"ok": True})
