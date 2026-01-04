import torch
from transformers import NougatProcessor, VisionEncoderDecoderModel

MODEL_NAME = "facebook/nougat-base"

_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

processor = NougatProcessor.from_pretrained(MODEL_NAME)
model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)
model.to(_device)
model.eval()

@torch.inference_mode()
def run_nougat(images):
    pixel_values = processor(images=images, return_tensors="pt").pixel_values
    pixel_values = pixel_values.to(_device)

    outputs = model.generate(
        pixel_values,
        max_length=4096,
        bad_words_ids=[[processor.tokenizer.unk_token_id]],
    )

    latex = processor.batch_decode(outputs, skip_special_tokens=True)[0]
    return latex