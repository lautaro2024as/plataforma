from __future__ import annotations

import json
import re
import shutil
import time
import zipfile
from pathlib import Path

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

PROJECT_BUNDLES = Path(settings.BASE_DIR) / "omega_wallpapers"
RUNTIME_ROOT = Path(settings.BASE_DIR) / "omega_data" / "wallpapers"
STATE_FILE = Path(settings.BASE_DIR) / "omega_data" / "wallpaper_state.json"


def _slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(value).stem).strip("._")
    return value or "wallpaper"


def _safe_extract(zf: zipfile.ZipFile, destination: Path) -> None:
    root = destination.resolve()
    for info in zf.infolist():
        name = info.filename.replace("\\", "/")
        if not name or name.startswith("/") or ".." in Path(name).parts:
            raise ValueError("ZIP contiene una ruta no segura.")
        target = (destination / name).resolve()
        if target != root and root not in target.parents:
            raise ValueError("ZIP intenta salir del directorio permitido.")
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info) as src, target.open("wb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)


def _project_json_in_zip(zf: zipfile.ZipFile) -> str | None:
    for name in zf.namelist():
        if Path(name).name.lower() == "project.json":
            return name
    return None


def _extract_bundle(bundle: Path, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle) as zf:
        if not _project_json_in_zip(zf):
            raise ValueError("El bundle no contiene project.json.")
        _safe_extract(zf, folder)


def _bootstrap_project_bundles() -> None:
    PROJECT_BUNDLES.mkdir(parents=True, exist_ok=True)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    for bundle in sorted(PROJECT_BUNDLES.glob("*.zip")):
        folder = RUNTIME_ROOT / bundle.stem
        project = folder / "project.json"
        if project.exists():
            continue
        try:
            _extract_bundle(bundle, folder)
        except (OSError, zipfile.BadZipFile, ValueError):
            continue


def _bundle_runtime(folder: Path) -> Path:
    PROJECT_BUNDLES.mkdir(parents=True, exist_ok=True)
    bundle = PROJECT_BUNDLES / f"{folder.name}.zip"
    if bundle.exists():
        return bundle
    temp = PROJECT_BUNDLES / f".{folder.name}.{time.time_ns()}.tmp.zip"
    try:
        with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for path in folder.rglob("*"):
                if path.is_file() and path.name != "__source.zip":
                    zf.write(path, path.relative_to(folder).as_posix())
        temp.replace(bundle)
        return bundle
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def _items():
    _bootstrap_project_bundles()
    items = []
    for bundle in sorted(PROJECT_BUNDLES.glob("*.zip")):
        folder = RUNTIME_ROOT / bundle.stem
        project = folder / "project.json"
        name = bundle.stem
        kind = "scene"
        if project.exists():
            try:
                data = json.loads(project.read_text(encoding="utf-8", errors="ignore"))
                name = data.get("title") or name
                kind = data.get("type") or "scene"
            except (OSError, ValueError):
                pass
        if project.exists():
            items.append({
                "id": f"portable-{bundle.stem}",
                "name": name,
                "file": str(project),
                "kind": kind,
                "source": "portable",
                "bundle": str(bundle),
            })
    return items


def _active():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def _store_active(item: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({
        "id": item["id"],
        "file": item["file"],
        "name": item["name"],
        "source": item["source"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def _runtime_folder_from_id(wallpaper_id: str) -> Path:
    if not wallpaper_id.startswith("portable-"):
        raise ValueError("ID no portátil")
    name = wallpaper_id[len("portable-"):]
    if not name or Path(name).name != name or ".." in Path(name).parts:
        raise ValueError("ID de wallpaper inválido")
    folder = (RUNTIME_ROOT / name).resolve()
    root = RUNTIME_ROOT.resolve()
    if folder != root and root not in folder.parents:
        raise ValueError("Wallpaper fuera del directorio permitido")
    return folder


@staff_member_required
def panel(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Solo el superusuario puede controlar wallpapers."}, status=403)
    return render(request, "admin/omega_portable_wallpaper.html", {
        "wallpapers": _items(),
        "active": _active(),
    })


@staff_member_required
@require_GET
def listing(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    return JsonResponse({"items": _items(), "active": _active()})


@staff_member_required
@require_POST
def import_bundle(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    uploaded = request.FILES.get("file")
    if not uploaded or not uploaded.name.lower().endswith(".zip"):
        return JsonResponse({"detail": "Seleccioná un ZIP de Wallpaper Engine."}, status=400)
    if uploaded.size > 500 * 1024 * 1024:
        return JsonResponse({"detail": "El ZIP supera 500 MB."}, status=400)

    PROJECT_BUNDLES.mkdir(parents=True, exist_ok=True)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    stem = _slug(uploaded.name)
    bundle = PROJECT_BUNDLES / f"{stem}.zip"
    index = 2
    while bundle.exists():
        stem = f"{_slug(uploaded.name)}_{index}"
        bundle = PROJECT_BUNDLES / f"{stem}.zip"
        index += 1
    tmp = PROJECT_BUNDLES / f".{stem}.uploading"
    folder = RUNTIME_ROOT / stem
    try:
        with tmp.open("wb") as out:
            for chunk in uploaded.chunks():
                out.write(chunk)
        with zipfile.ZipFile(tmp) as zf:
            if not _project_json_in_zip(zf):
                raise ValueError("No se encontró project.json dentro del ZIP.")
        if folder.exists():
            shutil.rmtree(folder)
        _extract_bundle(tmp, folder)
        tmp.replace(bundle)
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        tmp.unlink(missing_ok=True)
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
        return JsonResponse({"detail": f"No se pudo guardar: {exc}"}, status=400)
    return JsonResponse({"ok": True, "id": f"portable-{stem}", "name": stem, "bundle": str(bundle), "message": "Wallpaper guardado dentro del proyecto."})


@staff_member_required
@require_POST
def activate(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    try:
        payload = json.loads(request.body or "{}")
        wallpaper_id = str(payload.get("id", ""))
        folder = _runtime_folder_from_id(wallpaper_id)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return JsonResponse({"detail": str(exc) or "ID inválido."}, status=400)

    if not folder.is_dir():
        bundle = PROJECT_BUNDLES / f"{wallpaper_id[len('portable-'):]}.zip"
        if not bundle.exists():
            return JsonResponse({"detail": "El bundle no existe dentro del proyecto."}, status=404)
        try:
            _extract_bundle(bundle, folder)
        except (OSError, zipfile.BadZipFile, ValueError) as exc:
            return JsonResponse({"detail": f"No se pudo preparar el wallpaper: {exc}"}, status=400)

    project = folder / "project.json"
    if not project.exists():
        return JsonResponse({"detail": "El wallpaper no contiene project.json."}, status=400)

    item = next((x for x in _items() if x["id"] == wallpaper_id), None)
    if item is None:
        item = {"id": wallpaper_id, "name": folder.name, "file": str(project), "kind": "scene", "source": "portable", "bundle": str(PROJECT_BUNDLES / f"{folder.name}.zip")}
    try:
        bundle = _bundle_runtime(folder)
    except OSError as exc:
        return JsonResponse({"detail": f"No se pudo crear el bundle: {exc}"}, status=500)
    _store_active(item)
    return JsonResponse({"ok": True, "id": wallpaper_id, "portable": True, "bundle": str(bundle), "message": "Wallpaper activo y guardado dentro del proyecto."})


@staff_member_required
@require_GET
def preview(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    wallpaper_id = str(request.GET.get("id", ""))
    try:
        folder = _runtime_folder_from_id(wallpaper_id) if wallpaper_id else None
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    if folder is None or not folder.exists():
        active = _active() or {}
        try:
            folder = _runtime_folder_from_id(str(active.get("id", "")))
        except ValueError:
            folder = None
    if folder is None:
        return JsonResponse({"detail": "Seleccioná primero un wallpaper."}, status=404)
    for pattern in ("preview.gif", "preview.png", "preview.jpg", "preview.jpeg"):
        candidates = list(folder.rglob(pattern))
        if candidates:
            path = candidates[0]
            content_type = {".gif":"image/gif", ".png":"image/png", ".jpg":"image/jpeg", ".jpeg":"image/jpeg"}.get(path.suffix.lower(), "application/octet-stream")
            return FileResponse(path.open("rb"), content_type=content_type)
    return JsonResponse({"detail": "No hay preview en este wallpaper."}, status=404)
