from io import BytesIO

import numpy as np
from PIL import Image, ImageOps


def normalize_image(content: bytes, size: tuple[int, int], mean: list[float], std: list[float]):
    import torch

    with Image.open(BytesIO(content)) as source:
        source.verify()
    with Image.open(BytesIO(content)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image = image.resize(size, Image.Resampling.BILINEAR)
        array = np.asarray(image, dtype=np.float32) / 255.0
    array = (array - np.asarray(mean, dtype=np.float32)) / np.asarray(std, dtype=np.float32)
    tensor = torch.from_numpy(array).permute(2, 0, 1).unsqueeze(0).contiguous()
    return tensor


def sanitize_image(content: bytes, max_side: int = 2048) -> tuple[bytes, tuple[int, int]]:
    with Image.open(BytesIO(content)) as source:
        source.verify()
    with Image.open(BytesIO(content)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        width, height = image.size
        longest = max(width, height)
        if longest > max_side:
            scale = max_side / longest
            image = image.resize(
                (max(1, round(width * scale)), max(1, round(height * scale))),
                Image.Resampling.LANCZOS,
            )
        image.info.clear()
        output = BytesIO()
        image.save(output, format="JPEG", quality=90, optimize=True)
        return output.getvalue(), image.size
