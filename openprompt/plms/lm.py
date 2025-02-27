from transformers.tokenization_utils import PreTrainedTokenizer
from openprompt.plms.utils import TokenizerWrapper
from typing import List, Dict, Optional
from collections import defaultdict
import numpy as np
from openprompt.utils.logging import logger


class LMTokenizerWrapper(TokenizerWrapper):
    r"""
    LMTokenizer is a causual language model. Therefore it can only predict <mask> position
    at the end of the sentence. A prefix-style template like: 'A <mask> news : <text_a> <text_b> ' is 
    not applicable in this situation. 
    For the template where there is '<text_a>' or '<text_b>' after '<mask>', we raise an exception and terminate
    the program. 
    For the template where there are template words after '<mask>', we ignore these template words.
    Moreover, it can only predict one '<mask>' position. All template that has multiple '<mask>' will 
    give rise to an exception.
    """
    def __init__(self,
                 max_seq_length: int,
                 tokenizer: PreTrainedTokenizer,
                 truncate_method: Optional[str] = 'tail',
                 predict_eos_token: Optional[bool] = False,
                 **kwargs):
        super().__init__(max_seq_length=max_seq_length, tokenizer=tokenizer,truncate_method=truncate_method)
        self.predict_eos = predict_eos_token
    @property
    def num_special_tokens_to_add(self):
        if not hasattr(self, '_num_specials'):
            self._num_specials = self.tokenizer.num_special_tokens_to_add()
        return self._num_specials


    def tokenize_one_example(self, wrapped_example, teacher_forcing):
        ''' # TODO doens't consider the situation that input has two parts
        '''
        wrapped_example, others = wrapped_example

        if teacher_forcing:
            
            tgt_text = others['tgt_text']
            if isinstance(tgt_text, str):
                tgt_text = [tgt_text]
            

        encoder_inputs = defaultdict(list)

        num_mask_token_used = 0
        
        add_prefix_space = " "# Whether adding a space before the first word.
        for piece_id, piece in enumerate(wrapped_example):
            if len(piece['text']) == 0:
                continue
        
            if piece['text'] == self.template_eos_token and wrapped_example[piece_id-1]['loss_ids'] == 1: # eos after the mask also need to be pred
                piece['loss_ids'] = 1

            if piece['text'] == self.template_mask_token:
                if teacher_forcing:
                    piece['text'] = tgt_text[num_mask_token_used]
                else:
                    encoder_inputs['loss_ids'][-1][-1] = 1
                    break

            if piece['text'] in self.special_tokens_maps.keys():
                piece['text'] = self.special_tokens_maps[piece['text']]

            if 'new_token_ids' in piece and piece['new_token_ids']!=0:
                encode_text =  [0] # can be replace by any token, since these token will use their own embeddings
            else: 
                encode_text = self.tokenizer.encode(add_prefix_space + piece['text'], add_special_tokens=False)
            
            add_prefix_space = " "
            encoding_length = len(encode_text)
            
            encoder_inputs['input_ids'].append(encode_text)
            for key in piece:
                if key!='text':
                    encoder_inputs[key].append([piece[key]]*encoding_length)

        encoder_inputs = self.truncate(encoder_inputs=encoder_inputs)

        # delete shortenable ids
        encoder_inputs.pop("shortenable_ids")
        encoder_inputs = self.concate_parts(input_dict=encoder_inputs)
        encoder_inputs = self.add_special_tokens(encoder_inputs=encoder_inputs)
        # create special input ids
        encoder_inputs['attention_mask'] = [1] *len(encoder_inputs['input_ids'])
        encoder_inputs['token_type_ids'] = [0] *len(encoder_inputs['input_ids'])
        
        encoder_inputs = self.padding(input_dict=encoder_inputs, max_len=self.max_seq_length)
        encoder_inputs = dict(encoder_inputs)
        return encoder_inputs
    