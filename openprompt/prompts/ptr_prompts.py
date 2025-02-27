
import json
from openprompt.data_utils.data_utils import InputFeatures
import os
import torch
from torch import nn
from typing import *
from transformers import PreTrainedModel
from transformers.tokenization_utils import PreTrainedTokenizer
from openprompt import Template, Verbalizer
from openprompt.prompts import ManualTemplate, ManualVerbalizer, PtuningTemplate

class PTRTemplate(PtuningTemplate):
    """
    Args:
        model (:obj:`PreTrainedModel`): The pre-trained language model for the current prompt-learning task.
        tokenizer (:obj:`PreTrainedTokenizer`): A tokenizer to appoint the vocabulary and the tokenization strategy.
        text (:obj:`Optional[List[str]]`, optional): manual template format. Defaults to None.
        mask_token (:obj:`str`, optional): The special token that is masked and need to be predicted by the model. Default to ``<mask>``
        new_token (:obj:`str`, optional): The special token for new token. Default to ``<new>``
        placeholder_mapping (:obj:`dict`): A place holder to represent the original input text. Default to ``{'<text_a>': 'text_a', '<text_b>': 'text_b'}``
    """
    def __init__(self, 
                 model: PreTrainedModel,
                 tokenizer: PreTrainedTokenizer,
                 text:  Optional[str] = None,
                 mask_token: str = '<mask>',
                 new_token: str = '<new>',
                 placeholder_mapping: dict = {'<text_a>':'text_a', '<text_b>':'text_b'},
                ):
        super().__init__(model=model,
                         tokenizer=tokenizer,
                         prompt_encoder_type="mlp",
                         text=text,
                         mask_token=mask_token,
                         new_token=new_token,
                         placeholder_mapping=placeholder_mapping)

    def on_text_set(self):
        r"""
        when template text was set, generate parameter needed in p-tuning input embedding phrase
        """
        super().on_text_set()
        self.mask_count = 0
        for token in self.text:
            if token == self.mask_token:
                self.mask_count += 1

class PTRVerbalizer(Verbalizer):
    """
    Args: 
        tokenizer (:obj:`PreTrainedTokenizer`): A tokenizer to appoint the vocabulary and the tokenization strategy.
        classes (:obj:`Sequence[str]`): A sequence of classes that need to be projected.
        label_words (:obj:`Union[Sequence[str], Mapping[str, str]]`, optional): The label words that are projected by the labels.
    """
    def __init__(self,
                 tokenizer: PreTrainedTokenizer,
                 classes: Sequence[str] = None,
                 num_classes: Optional[int] = None,
                 label_words: Optional[Union[Sequence[Sequence[str]], Mapping[str, Sequence[str]]]] = None,
                ):
        super().__init__(tokenizer = tokenizer, classes = classes, num_classes = num_classes)
        self.label_words = label_words

    def on_label_words_set(self):
        super().on_label_words_set()

        self.num_masks = len(self.label_words[0])
        for words in self.label_words:
            if len(words) != self.num_masks:
                raise ValueError("number of mask tokens for different classes are not consistent")
        self.sub_labels = [
            list(set([words[i] for words in self.label_words]))
            for i in range(self.num_masks)
        ] # [num_masks, label_size of the corresponding mask]

        self.verbalizers = nn.ModuleList([
            ManualVerbalizer(tokenizer=self.tokenizer, label_words=labels)
            for labels in self.sub_labels
        ]) # [num_masks]

        self.label_mappings = nn.Parameter(torch.LongTensor([
            [labels.index(words[j]) for words in self.label_words]
            for j, labels in enumerate(self.sub_labels)
        ]), requires_grad=False) # [num_masks, label_size of the whole task]

    def process_logits(self,
                       logits: torch.Tensor, # [batch_size, num_masks, vocab_size]
                       batch: InputFeatures,
                       **kwargs):
        each_logits = [ # logits of each verbalizer
            self.verbalizers[i].process_logits(logits=logits[:, i, :], batch=batch, **kwargs)
            for i in range(self.num_masks)
        ] # num_masks * [batch_size, label_size of the corresponding mask]

        label_logits = [ # (logits of each label) of each mask
            logits[:, self.label_mappings[j]]
            for j, logits in enumerate(each_logits)
        ] # num_masks * [batch_size, label_size of the whole mask]

        label_logits = sum(label_logits) # [batch_size, label_size of the whole mask]
        # TODO test needed

        return label_logits