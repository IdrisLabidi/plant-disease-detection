import numpy as np
import torch
from PIL import Image


def classify(model, card, tensor):
    with torch.inference_mode():
        logits = model(tensor)
        if isinstance(logits, tuple):
            logits = logits[0]
        if card.softmax_inside_model:
            probabilities = logits
        else:
            probabilities = torch.softmax(logits, dim=1)
        probabilities = probabilities.squeeze(0).cpu()
    values = probabilities.tolist()
    if card.classes:
        if len(card.classes) != len(values):
            raise ValueError("Model class count does not match model card")
        pairs = list(zip(card.classes, values, strict=False))
    else:
        pairs = [(f"class_{index}", value) for index, value in enumerate(values)]
    pairs.sort(key=lambda item: item[1], reverse=True)
    top3 = [{"class_name": name, "probability": float(prob)} for name, prob in pairs[:3]]
    top1 = top3[0]["probability"]
    unsure = card.unsure_threshold is not None and top1 < card.unsure_threshold
    return top3, unsure


def segment(model, card, tensor):
    with torch.inference_mode():
        output = model(tensor)
        if isinstance(output, tuple):
            output = output[0]
        if output.dim() == 4:
            if card.softmax_inside_model:
                probabilities = output[:, 1]
            else:
                probabilities = torch.softmax(output, dim=1)[:, 1]
        else:
            probabilities = torch.sigmoid(output)
        mask = probabilities.squeeze().cpu()
    lesion_mask = mask >= card.mask_threshold
    lesion = float(lesion_mask.float().mean().item())
    lesion_np = lesion_mask.numpy()
    rgba = np.zeros((lesion_np.shape[0], lesion_np.shape[1], 4), dtype=np.uint8)
    rgba[lesion_np] = (239, 68, 68, 255)
    mask_image = Image.fromarray(rgba, mode="RGBA").resize(
        (tensor.shape[-1], tensor.shape[-2]),
        Image.Resampling.NEAREST,
    )
    return lesion, mask_image
