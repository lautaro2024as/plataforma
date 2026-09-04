from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse

from . import omega_portable as core


def _migrate_runtime_to_project() -> None:
    """Promote old runtime wallpapers into portable project bundles."""
    core.PROJECT_BUNDLES.mkdir(parents=True, exist_ok=True)
    core.RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    for folder in core.RUNTIME_ROOT.iterdir():
        if not folder.is_dir():
            continue
        bundle = core.PROJECT_BUNDLES / f"{folder.name}.zip"
        project = folder / "project.json"
        if project.exists() and not bundle.exists():
            try:
                core._bundle_runtime(folder)
            except OSError:
                pass


@staff_member_required
def panel(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Solo el superusuario puede controlar wallpapers."}, status=403)
    _migrate_runtime_to_project()
    return core.panel(request)


@staff_member_required
def listing(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    _migrate_runtime_to_project()
    return core.listing(request)


@staff_member_required
def import_bundle(request):
    return core.import_bundle(request)


@staff_member_required
def activate(request):
    _migrate_runtime_to_project()
    return core.activate(request)


@staff_member_required
def delete_bundle(request):
    _migrate_runtime_to_project()
    return core.delete_bundle(request)


@staff_member_required
def preview(request):
    _migrate_runtime_to_project()
    return core.preview(request)
