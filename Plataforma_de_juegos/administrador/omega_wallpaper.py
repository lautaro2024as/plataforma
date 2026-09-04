import json
import os
import re
import shutil
import subprocess
import time
import zipfile
from pathlib import Path
from urllib.parse import unquote

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

CACHE = {"at": 0.0, "items": [], "exe": None}
CACHE_TTL = 30
PORTABLE_ROOT = Path(settings.BASE_DIR) / "omega_data" / "wallpapers"
PROJECT_BUNDLES = Path(settings.BASE_DIR) / "omega_wallpapers"
STATE_FILE = Path(settings.BASE_DIR) / "omega_data" / "wallpaper_state.json"


def _steam_root():
    if os.name != "nt":
        return None
    try:
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for key_path in (r"Software\Valve\Steam", r"Software\WOW6432Node\Valve\Steam"):
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
                    items.append({"id": folder.name, "name": folder.name, "file": str(project), "kind": "project", "source": "steam"})
                    continue
                videos = list(folder.glob("*.mp4")) + list(folder.glob("*.webm"))
                if videos:
                    items.append({"id": folder.name, "name": folder.name, "file": str(videos[0]), "kind": "video", "source": "steam"})
    PORTABLE_ROOT.mkdir(parents=True, exist_ok=True)
    for folder in PORTABLE_ROOT.iterdir():
        if not folder.is_dir():
            continue
        project = folder / "project.json"
        if project.exists():
            try:
                data = json.loads(project.read_text(encoding="utf-8", errors="ignore"))
                name = data.get("title") or folder.name
                kind = data.get("type", "scene")
            except (OSError, ValueError):
                name, kind = folder.name, "unknown"
            items.append({"id": f"portable-{folder.name}", "name": name, "file": str(project), "kind": kind, "source": "portable"})
        else:
            videos = list(folder.glob("*.mp4")) + list(folder.glob("*.webm"))
            if videos:
                items.append({"id": f"portable-{folder.name}", "name": folder.name, "file": str(videos[0]), "kind": "video", "source": "portable"})
    items.sort(key=lambda x: x["name"].lower())
    CACHE.update({"at": now, "items": items, "exe": exe})
    return items, exe


def _safe_extract(zip_file, destination):
    destination = destination.resolve()
    for info in zip_file.infolist():
        raw_name = info.filename.replace("\\", "/")
        if not raw_name or raw_name.startswith("/") or ".." in Path(raw_name).parts:
            raise ValueError("ZIP contiene una ruta no segura.")
        target = (destination / raw_name).resolve()
        if destination != target and destination not in target.parents:
            raise ValueError("ZIP contiene una ruta fuera del directorio permitido.")
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with zip_file.open(info) as source, target.open("wb") as output:
            while chunk := source.read(1024 * 1024):
                output.write(chunk)


def _store_active(item):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"id": item["id"], "file": item["file"], "name": item["name"], "source": item["source"]}, ensure_ascii=False, indent=2), encoding="utf-8")


def _portable_name(value):
    raw = unquote(str(value or "")).strip().replace("\\", "/")
    while raw.lower().startswith("portable-"):
        raw = raw[len("portable-"):]
    raw = raw.strip("/")
    if not raw or raw in {".", ".."} or "/" in raw or ".." in Path(raw).parts:
        raise ValueError("ID de wallpaper inválido")
    return raw


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
@require_GET
def wallpaper_preview(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    PORTABLE_ROOT.mkdir(parents=True, exist_ok=True)
    candidates = []
    for pattern in ("preview.gif", "preview.png", "preview.jpg", "preview.jpeg"):
        candidates.extend(PORTABLE_ROOT.rglob(pattern))
    if not candidates:
        return JsonResponse({"detail": "No hay preview importado."}, status=404)
    path = candidates[0]
    content_type = {".gif": "image/gif", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path.open("rb"), content_type=content_type)


@staff_member_required
@require_POST
def wallpaper_import(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    uploaded = request.FILES.get("file")
    if not uploaded or not uploaded.name.lower().endswith(".zip"):
        return JsonResponse({"detail": "Selecciona el ZIP completo del wallpaper."}, status=400)
    if uploaded.size > 300 * 1024 * 1024:
        return JsonResponse({"detail": "El ZIP supera el límite de 300 MB."}, status=400)
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "_", Path(uploaded.name).stem).strip("._") or "wallpaper"
    target = PORTABLE_ROOT / stem
    n = 2
    while target.exists():
        target = PORTABLE_ROOT / f"{stem}_{n}"
        n += 1
    target.mkdir(parents=True, exist_ok=False)
    temp = target / "__source.zip"
    try:
        with temp.open("wb") as output:
            for chunk in uploaded.chunks():
                output.write(chunk)
        with zipfile.ZipFile(temp) as zf:
            if not any(Path(name).name.lower() == "project.json" for name in zf.namelist()):
                raise ValueError("No se encontró project.json; no parece un paquete exportable de Wallpaper Engine.")
            _safe_extract(zf, target)
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        shutil.rmtree(target, ignore_errors=True)
        return JsonResponse({"detail": f"No se pudo importar: {exc}"}, status=400)
    finally:
        temp.unlink(missing_ok=True)
    CACHE["at"] = 0
    return JsonResponse({"ok": True, "name": stem})


@staff_member_required
@require_POST
def wallpaper_set(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    try:
        payload = json.loads(request.body or "{}")
        target_id = str(payload.get("id", ""))
        target_file = str(payload.get("file", ""))
    except (ValueError, TypeError):
        return JsonResponse({"detail": "JSON inválido."}, status=400)

    items, exe = _discover()
    item = next((x for x in items if target_id and x["id"] == target_id), None)
    if item is None and target_file:
        try:
            normalized = str(Path(target_file).resolve())
        except OSError:
            normalized = target_file
        item = next((x for x in items if str(Path(x["file"]).resolve()) == normalized), None)

    if item is None:
        return JsonResponse({"detail": "Wallpaper no registrado por OMEGA. Actualizá la página y probá nuevamente."}, status=404)

    _store_active(item)
    if item["source"] == "portable":
        return JsonResponse({"ok": True, "file": item["file"], "id": item["id"], "portable": True, "message": "Fondo portátil seleccionado y guardado en OMEGA."})

    if not exe:
        return JsonResponse({"detail": "No se encontró wallpaper64.exe."}, status=503)
    try:
        subprocess.Popen([exe, "-control", "openWallpaper", "-file", item["file"]], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        return JsonResponse({"detail": f"No se pudo iniciar Wallpaper Engine: {exc}"}, status=500)
    return JsonResponse({"ok": True, "file": item["file"], "id": item["id"], "portable": False})


@staff_member_required
@require_POST
def wallpaper_delete(request):
    """Delete exactly the portable wallpaper represented by the rendered card.

    We deliberately resolve the folder from OMEGA's current discovery list instead of
    parsing the client-supplied ID. This prevents old/duplicated ID formats from ever
    reaching the filesystem and fixes the recurring 'ID de wallpaper inválido' error.
    """
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)

    try:
        payload = json.loads(request.body or "{}")
    except (ValueError, TypeError):
        return JsonResponse({"detail": "JSON inválido."}, status=400)

    target_id = str(payload.get("id", "")).strip()
    if not target_id:
        return JsonResponse({"detail": "No se recibió el fondo a eliminar."}, status=400)

    items, _ = _discover()
    item = next((x for x in items if x.get("source") == "portable" and x.get("id") == target_id), None)

    # Compatibility fallback for an old page that sends a duplicated portable- prefix.
    if item is None:
        clean_id = target_id
        while clean_id.lower().startswith("portable-"):
            clean_id = clean_id[len("portable-"):]
        item = next((x for x in items if x.get("source") == "portable" and (x.get("id") == f"portable-{clean_id}" or x.get("id") == clean_id)), None)

    if item is None:
        return JsonResponse({"detail": "No encontré ese fondo portátil en OMEGA. Recargá la página."}, status=404)

    try:
        target = Path(item["file"]).resolve().parent
        root = PORTABLE_ROOT.resolve()
        if target == root or root not in target.parents:
            return JsonResponse({"detail": "El fondo apunta fuera del almacenamiento portátil."}, status=400)

        # Remove the extracted runtime copy.
        shutil.rmtree(target)

        # Remove the portable project bundle too, so it does not reappear after restart.
        bundle = PROJECT_BUNDLES / f"{target.name}.zip"
        if bundle.exists():
            bundle.unlink()

        # Clear active state only if this exact portable folder was active.
        try:
            active = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            active = {}
        active_file = str(active.get("file", "")) if isinstance(active, dict) else ""
        if active_file:
            try:
                if Path(active_file).resolve().parent == target:
                    STATE_FILE.unlink(missing_ok=True)
            except OSError:
                pass
    except OSError as exc:
        return JsonResponse({"detail": f"No se pudo eliminar el fondo: {exc}"}, status=500)

    CACHE["at"] = 0
    return JsonResponse({"ok": True, "message": f"Fondo '{item['name']}' eliminado completamente de OMEGA."})
