import json
import re
from pathlib import Path

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST


MUSIC_ROOT = Path(settings.BASE_DIR) / "omega_data" / "music"
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
    return {
        "id": item["id"],
        "name": item["name"],
        "url": f"/admin/omega/music/stream/{item['id']}/",
        "size": item.get("size", 0),
    }


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


@staff_member_required
@require_GET
def music_stream(request, music_id):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    item = next((x for x in _read_library() if str(x.get("id")) == str(music_id)), None)
    if not item:
        return JsonResponse({"detail": "Tema no encontrado."}, status=404)
    path = MUSIC_ROOT / item.get("filename", "")
    if not path.exists() or not path.is_file():
        return JsonResponse({"detail": "Archivo de música no encontrado."}, status=404)
    return FileResponse(path.open("rb"), as_attachment=False, filename=item.get("name", path.name))


@staff_member_required
@require_POST
def music_delete(request, music_id):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    items = _read_library()
    item = next((x for x in items if str(x.get("id")) == str(music_id)), None)
    if not item:
        return JsonResponse({"detail": "Tema no encontrado."}, status=404)
    path = MUSIC_ROOT / item.get("filename", "")
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass
    _write_library([x for x in items if str(x.get("id")) != str(music_id)])
    return JsonResponse({"ok": True})
