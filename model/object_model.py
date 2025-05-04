from abc import ABC

import torch
import torchvision

print(torch.__version__)
print(torchvision.__version__)

from torch import nn
import pandas as pd
import io
import PIL.Image as Image
from transformers import SegformerFeatureExtractor, SegformerForSemanticSegmentation
from datetime import datetime

from model.processing_model_base import ProcessingModelBase


OBJECT_LABELS = pd.read_csv('./model/OBJECT_LABELS.csv')
MODEL_NAME = "nvidia/segformer-b5-finetuned-ade-640-640"


class ObjectModel(ProcessingModelBase, ABC):
    def __init__(self):
        self.feature_extractor = SegformerFeatureExtractor.from_pretrained(MODEL_NAME)
        self.model = SegformerForSemanticSegmentation.from_pretrained(MODEL_NAME)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        super().__init__()

    def process_data(self, bytes_data):
        started_time = datetime.now()
        image = Image.open(io.BytesIO(bytes_data)).convert('RGB')

        pixel_values = self.feature_extractor(image, return_tensors="pt").pixel_values.to(self.device)
        predict = self.model(pixel_values)
        logits = nn.functional.interpolate(predict.logits.detach().cpu(),
                                           size=image.size[::-1],
                                           mode='bilinear',
                                           align_corners=False)

        seg = logits.argmax(dim=1)[0]
        label_name = OBJECT_LABELS['name']
        labels = seg.unique()

        tags = []
        for label in labels:
            tags.append(label_name[int(label)])

        ended_time = datetime.now()
        print(f'TIME:{ended_time - started_time}')

        return [{'name': tag} for tag in tags]

