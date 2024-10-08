# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/02_rt_detr.finetuning.ipynb.

# %% auto 0
__all__ = ['create_val_dataset', 'idx_categories', 'get_ds_obj', 'show_bbox', 'DetectionDataset']

# %% ../../nbs/02_rt_detr.finetuning.ipynb 4
from datasets import load_dataset 
from datasets import DatasetDict
from fastcore.imports import *
from PIL import Image, ImageDraw
from typing import Any, Dict, List, Optional, Tuple, Union
import albumentations as A
from torch.utils.data import DataLoader, Dataset
import numpy as np

# %% ../../nbs/02_rt_detr.finetuning.ipynb 8
def create_val_dataset(
        dataset:DatasetDict,
        test_size:float=0.1):

    if 'validation' not in dataset:
        split = dataset["train"].train_test_split(test_size=test_size, seed=1137)
        dataset['train'] = split['train']
        dataset['validation'] = split['test']


    return dataset

# %% ../../nbs/02_rt_detr.finetuning.ipynb 12
def idx_categories(
        categories)->Tuple[Dict[int,str],Dict[str,int]]:
    'create id2label and label2id dictionaries'
    id2label = {i:cat for i,cat in enumerate(categories)}
    lbl2id = {cat:i for i,cat in enumerate(categories)}
    return id2label,lbl2id

# %% ../../nbs/02_rt_detr.finetuning.ipynb 14
def get_ds_obj(
        ds:DatasetDict, 
        split:str,
        idx:int=0
        ):
    img = ds[split][idx]['image']
    bbox = ds[split][idx]['objects']

    return img, bbox

# %% ../../nbs/02_rt_detr.finetuning.ipynb 15
def show_bbox(
        img:Image.Image, # Pil Image
        bbox:List[List[float]], # bounding box lists
        categories:List[int], # categories like [0,1,2,3,4]
        id2label:Dict[int,str] # id to label dictionary
        ):
    draw = ImageDraw.Draw(img)
    for box, cat in zip(bbox, categories):
        x, y, w, h = box
        draw.rectangle((x, y, x+w, y+h), outline='yellow', width=2)
        draw.text((x, y), id2label[cat], fill='yellow')
    return img

# %% ../../nbs/02_rt_detr.finetuning.ipynb 20
class DetectionDataset(Dataset):
    def __init__(
            self, 
            dataset:DatasetDict, 
            id2label:Dict[int,str], 
            lbl2id:Dict[str,int], 
            image_processor:Optional[Any]=None,
            transforms=None):
        self.dataset = dataset
        self.id2label = id2label
        self.lbl2id = lbl2id
        self.image_processor = image_processor
        self.transforms = transforms

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        img = self.dataset[idx]['image']
        image_id = self.dataset[idx]['image_id']

        labels = self.dataset[idx]['objects']
        bbox, cats = labels['bbox'], labels['category']
        img = np.array(img.convert('RGB'))
        if self.transforms:
            transformed = self.transforms(
                image=img,
                bboxes=bbox,
                category=cats)

            img = transformed['image']
            bbox = transformed['bboxes'] 
            cats = transformed['category']

        def format_as_coco(
                img_id:int, 
                categories:List[str],
                boxes:List[List[float]])->Dict[str,Any]:
            'format as coco dataset'

            annotations=[{'image_id':img_id, 'category_id':cate, 'bbox':list(box),'iscrowd':0, 'area':box[2]*box[3]}for cate, box in zip(categories, boxes)]
            return {'image_id':img_id, 'annotations':annotations}

        formatted_ann = format_as_coco(
            img_id=image_id, 
            categories=cats,
            boxes=bbox)

        result = self.image_processor(
            images=img, 
            annotations=formatted_ann,
            return_tensors="pt")

        # Remove batch dimension as image proecessor adds it
        result= {k: v[0] for k, v in result.items() }
        return result


