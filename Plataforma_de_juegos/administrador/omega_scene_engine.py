from __future__ import annotations

import io
import json
import math
import os
import re
import struct
from pathlib import Path

import lz4.block
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET
from PIL import Image

PORTABLE_ROOT = Path(settings.BASE_DIR) / "omega_data" / "wallpapers"
CACHE_ROOT = Path(settings.BASE_DIR) / "omega_data" / "cache" / "scene_frames"
CANVAS_SIZE = (1920, 1080)


def _safe_folder_from_id(wallpaper_id: str) -> Path:
    if not wallpaper_id.startswith("portable-"):
        raise Http404("Wallpaper no portable.")
    name = wallpaper_id[len("portable-"):]
    if not name or Path(name).name != name or ".." in Path(name).parts:
        raise Http404("Wallpaper inválido.")
    folder = (PORTABLE_ROOT / name).resolve()
    root = PORTABLE_ROOT.resolve()
    if root != folder and root not in folder.parents:
        raise Http404("Wallpaper fuera del directorio permitido.")
    if not folder.is_dir():
        raise Http404("Wallpaper no encontrado.")
    return folder


def _parse_pkg(pkg_path: Path) -> tuple[int, dict[str, tuple[int, int]], int]:
    with pkg_path.open("rb") as f:
        def pascal() -> str:
            raw = f.read(4)
            if len(raw) != 4:
                raise ValueError("PKG truncado")
            size = struct.unpack("<I", raw)[0]
            data = f.read(size)
            if len(data) != size:
                raise ValueError("PKG truncado")
            return data.decode("utf-8", errors="replace").rstrip("\x00").strip()

        pascal()  # PKGVxxxx
        raw_count = f.read(4)
        if len(raw_count) != 4:
            raise ValueError("PKG sin tabla")
        count = struct.unpack("<I", raw_count)[0]
        entries: dict[str, tuple[int, int]] = {}
        for _ in range(count):
            name = pascal()
            raw = f.read(8)
            if len(raw) != 8:
                raise ValueError("Tabla PKG truncada")
            offset, length = struct.unpack("<II", raw)
            entries[name] = (offset, length)
        return count, entries, f.tell()


def _read_entry(pkg_path: Path, table: tuple[dict[str, tuple[int, int]], int], name: str) -> bytes:
    entries, data_offset = table
    if name not in entries:
        raise KeyError(name)
    offset, length = entries[name]
    with pkg_path.open("rb") as f:
        f.seek(data_offset + offset)
        data = f.read(length)
    if len(data) != length:
        raise ValueError("Entrada PKG truncada")
    return data


def _u32(buf: bytes, pos: int) -> int:
    return struct.unpack_from("<I", buf, pos)[0]


def _i32(buf: bytes, pos: int) -> int:
    return struct.unpack_from("<i", buf, pos)[0]


def _rgb565(value: int) -> tuple[int, int, int]:
    return (
        ((value >> 11) & 31) * 255 // 31,
        ((value >> 5) & 63) * 255 // 63,
        (value & 31) * 255 // 31,
    )


def _decode_dxt1(data: bytes, width: int, height: int) -> bytes:
    out = bytearray(width * height * 4)
    cursor = 0
    for by in range((height + 3) // 4):
        for bx in range((width + 3) // 4):
            c0, c1 = struct.unpack_from("<HH", data, cursor)
            cursor += 4
            a = _rgb565(c0)
            b = _rgb565(c1)
            if c0 > c1:
                palette = [
                    (*a, 255), (*b, 255),
                    tuple((2 * a[i] + b[i]) // 3 for i in range(3)) + (255,),
                    tuple((a[i] + 2 * b[i]) // 3 for i in range(3)) + (255,),
                ]
            else:
                palette = [
                    (*a, 255), (*b, 255),
                    tuple((a[i] + b[i]) // 2 for i in range(3)) + (255,),
                    (0, 0, 0, 0),
                ]
            bits = _u32(data, cursor)
            cursor += 4
            for p in range(16):
                x = bx * 4 + (p % 4)
                y = by * 4 + (p // 4)
                if x >= width or y >= height:
                    continue
                pixel = palette[(bits >> (2 * p)) & 3]
                off = (y * width + x) * 4
                out[off:off + 4] = bytes(pixel)
    return bytes(out)


def _decode_dxt3(data: bytes, width: int, height: int) -> bytes:
    out = bytearray(width * height * 4)
    cursor = 0
    for by in range((height + 3) // 4):
        for bx in range((width + 3) // 4):
            alpha = data[cursor:cursor + 8]
            cursor += 8
            c0, c1 = struct.unpack_from("<HH", data, cursor)
            cursor += 4
            a = _rgb565(c0)
            b = _rgb565(c1)
            palette = [
                (*a, 255), (*b, 255),
                tuple((2 * a[i] + b[i]) // 3 for i in range(3)) + (255,),
                tuple((a[i] + 2 * b[i]) // 3 for i in range(3)) + (255,),
            ]
            bits = _u32(data, cursor)
            cursor += 4
            for p in range(16):
                x = bx * 4 + (p % 4)
                y = by * 4 + (p // 4)
                if x >= width or y >= height:
                    continue
                av = (alpha[p // 2] >> (4 * (p % 2))) & 0xF
                av = (av << 4) | av
                r, g, b, _ = palette[(bits >> (2 * p)) & 3]
                off = (y * width + x) * 4
                out[off:off + 4] = bytes((r, g, b, av))
    return bytes(out)


def _decode_dxt5(data: bytes, width: int, height: int) -> bytes:
    out = bytearray(width * height * 4)
    cursor = 0
    for by in range((height + 3) // 4):
        for bx in range((width + 3) // 4):
            a0, a1 = data[cursor], data[cursor + 1]
            alpha_bits = int.from_bytes(data[cursor + 2:cursor + 8], "little")
            cursor += 8
            if a0 > a1:
                alpha_palette = [a0, a1, (6 * a0 + a1) // 7, (5 * a0 + 2 * a1) // 7,
                                 (4 * a0 + 3 * a1) // 7, (3 * a0 + 4 * a1) // 7,
                                 (2 * a0 + 5 * a1) // 7, (a0 + 6 * a1) // 7]
            else:
                alpha_palette = [a0, a1, (4 * a0 + a1) // 5, (3 * a0 + 2 * a1) // 5,
                                 (2 * a0 + 3 * a1) // 5, (a0 + 4 * a1) // 5, 0, 255]
            c0, c1 = struct.unpack_from("<HH", data, cursor)
            cursor += 4
            a = _rgb565(c0)
            b = _rgb565(c1)
            palette = [
                (*a, 255), (*b, 255),
                tuple((2 * a[i] + b[i]) // 3 for i in range(3)) + (255,),
                tuple((a[i] + 2 * b[i]) // 3 for i in range(3)) + (255,),
            ]
            bits = _u32(data, cursor)
            cursor += 4
            for p in range(16):
                x = bx * 4 + (p % 4)
                y = by * 4 + (p // 4)
                if x >= width or y >= height:
                    continue
                color = palette[(bits >> (2 * p)) & 3]
                av = alpha_palette[(alpha_bits >> (3 * p)) & 7]
                off = (y * width + x) * 4
                out[off:off + 4] = bytes((color[0], color[1], color[2], av))
    return bytes(out)


def _parse_tex(buf: bytes) -> Image.Image:
    if not buf.startswith(b"TEXV"):
        raise ValueError("No es TEXV")
    texi = buf.find(b"TEXI")
    if texi < 0:
        raise ValueError("TEXI no encontrado")
    pos = texi + 8
    while pos < len(buf) and buf[pos] == 0:
        pos += 1
    fmt = _i32(buf, pos); pos += 4
    pos += 4  # flags
    tex_w = _i32(buf, pos); pos += 4
    tex_h = _i32(buf, pos); pos += 4
    img_w = _i32(buf, pos); pos += 4
    img_h = _i32(buf, pos); pos += 4
    pos += 4  # clear color

    texb = buf.find(b"TEXB", pos)
    if texb < 0:
        raise ValueError("TEXB no encontrado")
    tag = buf[texb:texb + 8].decode("ascii", errors="ignore")
    version = int(tag[4:])
    pos = texb + 8
    while pos < len(buf) and buf[pos] == 0:
        pos += 1
    image_count = _i32(buf, pos); pos += 4
    image_fmt = _i32(buf, pos) if version >= 3 else -1
    if version >= 3:
        pos += 4
    if version >= 4:
        pos += 4  # mp4 flag

    best: Image.Image | None = None
    for _ in range(image_count):
        mip_count = _i32(buf, pos); pos += 4
        for mip in range(mip_count):
            mw = _i32(buf, pos); pos += 4
            mh = _i32(buf, pos); pos += 4
            is_lz4 = _i32(buf, pos) == 1; pos += 4
            decoded_size = _i32(buf, pos); pos += 4
            byte_count = _i32(buf, pos); pos += 4
            raw = buf[pos:pos + byte_count]
            pos += byte_count
            if mip != 0:
                continue
            if is_lz4:
                raw = lz4.block.decompress(raw, uncompressed_size=decoded_size)
            actual_fmt = fmt
            if actual_fmt == 5 and len(raw) == ((mw + 3) // 4) * ((mh + 3) // 4) * 8:
                actual_fmt = 7
            if actual_fmt in (0, 1):
                if len(raw) >= mw * mh * 4:
                    best = Image.frombytes("RGBA", (mw, mh), raw[:mw * mh * 4])
            elif actual_fmt in (4, 5):
                expected = ((mw + 3) // 4) * ((mh + 3) // 4) * 16
                if len(raw) == expected:
                    best = Image.frombytes("RGBA", (mw, mh), _decode_dxt5(raw, mw, mh))
            elif actual_fmt == 6:
                expected = ((mw + 3) // 4) * ((mh + 3) // 4) * 16
                if len(raw) == expected:
                    best = Image.frombytes("RGBA", (mw, mh), _decode_dxt3(raw, mw, mh))
            elif actual_fmt == 7:
                expected = ((mw + 3) // 4) * ((mh + 3) // 4) * 8
                if len(raw) == expected:
                    best = Image.frombytes("RGBA", (mw, mh), _decode_dxt1(raw, mw, mh))
            elif actual_fmt == 8 and len(raw) >= mw * mh * 2:
                rgba = bytearray(mw * mh * 4)
                for i in range(mw * mh):
                    rgba[i * 4:i * 4 + 4] = bytes((raw[i * 2], raw[i * 2 + 1], 0, 255))
                best = Image.frombytes("RGBA", (mw, mh), bytes(rgba))
            elif actual_fmt == 9 and len(raw) >= mw * mh:
                rgba = bytearray(mw * mh * 4)
                for i, value in enumerate(raw[:mw * mh]):
                    rgba[i * 4:i * 4 + 4] = bytes((value, value, value, 255))
                best = Image.frombytes("RGBA", (mw, mh), bytes(rgba))
    if best is None:
        raise ValueError("No se pudo decodificar TEX")
    return best


def _parse_vec(value: object, default: tuple[float, float] = (0.0, 0.0)) -> tuple[float, float]:
    if not isinstance(value, str):
        return default
    try:
        parts = [float(x) for x in value.split()]
        return parts[0], parts[1]
    except (ValueError, IndexError):
        return default


def _numeric_scale(value: object) -> tuple[float, float]:
    if isinstance(value, str):
        x, y = _parse_vec(value, (1.0, 1.0))
        return x, y
    return 1.0, 1.0


def _texture_for_model(pkg_path: Path, table: tuple[dict[str, tuple[int, int]], int], model_path: str) -> tuple[str, bool]:
    model = json.loads(_read_entry(pkg_path, table, model_path).decode("utf-8", errors="replace"))
    puppet = bool(model.get("puppet"))
    material_path = model.get("material")
    if not material_path:
        raise KeyError("model material")
    material = json.loads(_read_entry(pkg_path, table, material_path).decode("utf-8", errors="replace"))
    passes = material.get("passes") or []
    for render_pass in passes:
        textures = render_pass.get("textures") or []
        if textures and textures[0]:
            texture = str(textures[0])
            if not texture.endswith(".tex"):
                texture += ".tex"
            if not texture.startswith("materials/"):
                texture = "materials/" + texture
            return texture.replace("\\", "/"), puppet
    raise KeyError("material texture")


def render_scene_frame(folder: Path) -> Path:
    pkg_path = next(folder.glob("*.pkg"), None)
    if pkg_path is None:
        raise FileNotFoundError("No se encontró scene.pkg")

    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    stat = pkg_path.stat()
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", folder.name)
    cache = CACHE_ROOT / f"{slug}_{stat.st_size}_{stat.st_mtime_ns}.webp"
    if cache.exists():
        return cache

    _, entries, data_offset = _parse_pkg(pkg_path)
    table = (entries, data_offset)
    scene = json.loads(_read_entry(pkg_path, table, "scene.json").decode("utf-8", errors="replace"))

    base = Image.new("RGBA", CANVAS_SIZE, (2, 5, 16, 255))
    objects = scene.get("objects") or []

    # Render regular image layers only. Puppet/model layers are deliberately ignored,
    # so the central character from the original wallpaper cannot appear as a second character.
    layers: list[tuple[int, dict, Image.Image, tuple[float, float]]] = []
    for obj in objects:
        model_path = obj.get("image")
        if not isinstance(model_path, str) or not model_path.endswith(".json"):
            continue
        try:
            texture_path, puppet = _texture_for_model(pkg_path, table, model_path)
        except Exception:
            continue
        if puppet:
            continue
        if str(obj.get("name", "")).strip().lower() in {"rw", "audio bar", "纯色", "后处理层"}:
            continue
        try:
            texture = _parse_tex(_read_entry(pkg_path, table, texture_path))
        except Exception:
            continue
        ox, oy = _parse_vec(obj.get("origin"), (960.0, 540.0))
        sx, sy = _numeric_scale(obj.get("scale"))
        size_x, size_y = _parse_vec(obj.get("size"), (texture.width, texture.height))
        size_x = max(1.0, abs(size_x * sx))
        size_y = max(1.0, abs(size_y * sy))
        try:
            texture = texture.resize((int(size_x), int(size_y)), Image.Resampling.LANCZOS)
        except Exception:
            continue
        layers.append((int(obj.get("id", 0)), obj, texture, (ox, oy)))

    layers.sort(key=lambda item: item[0])
    for _, obj, image, (ox, oy) in layers:
        left = int(round(ox - image.width / 2 - (1920 - CANVAS_SIZE[0]) / 2))
        top = int(round(oy - image.height / 2 - (1080 - CANVAS_SIZE[1]) / 2))
        overlay = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        overlay.alpha_composite(image, (left, top))
        base = Image.alpha_composite(base, overlay)

    # Keep the dashboard readable without introducing the unwanted original character.
    grade = Image.new("RGBA", CANVAS_SIZE, (13, 8, 35, 70))
    base = Image.alpha_composite(base, grade)
    base = base.resize(CANVAS_SIZE, Image.Resampling.LANCZOS).convert("RGB")
    base.save(cache, "WEBP", quality=88, method=4)
    return cache


@staff_member_required
@require_GET
def scene_frame(request, wallpaper_id: str):
    if not request.user.is_superuser:
        raise Http404("No disponible.")
    folder = _safe_folder_from_id(wallpaper_id)
    try:
        frame = render_scene_frame(folder)
    except (FileNotFoundError, KeyError, ValueError, OSError, json.JSONDecodeError, lz4.block.LZ4BlockError) as exc:
        raise Http404(f"No se pudo renderizar el wallpaper: {exc}") from exc
    response = FileResponse(frame.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "no-store"
    return response
