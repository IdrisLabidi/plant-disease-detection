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
    lesion = float((mask >= card.mask_threshold).float().mean().item())
    mask_bytes = Image.fromarray((mask.numpy() * 255).astype("uint8")).resize(
        (tensor.shape[-1], tensor.shape[-2]),
        Image.Resampling.NEAREST,
    )
    return lesion, mask_bytes
