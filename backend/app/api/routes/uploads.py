"""Görsel yükleme: bilgisayardan dosya yükle, statik URL döndür."""

from __future__ import annotations

import pathlib
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import require_manager
from app.models.user import User

router = APIRouter(prefix="/uploads", tags=["uploads"])

RequireManager = Annotated[User, Depends(require_manager)]

# Yüklenen dosyalar buraya kaydedilir; main.py /api/v1/media altında servis eder.
UPLOAD_DIR = pathlib.Path("/app/uploads")

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/image")
async def upload_image(
    _: RequireManager,
    file: Annotated[UploadFile, File()],
) -> dict[str, str]:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece JPEG, PNG, WEBP veya GIF görseller yüklenebilir",
        )

    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Görsel en fazla 5 MB olabilir",
        )

    ext = ALLOWED_TYPES[file.content_type]
    name = f"{uuid.uuid4().hex}{ext}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / name).write_bytes(contents)

    return {"url": f"/api/v1/media/{name}"}
