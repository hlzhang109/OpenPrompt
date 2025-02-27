from yacs.config import CfgNode
from openprompt.utils.utils import signature
from re import TEMPLATE
from typing import Optional
from transformers.tokenization_utils import PreTrainedTokenizer

from transformers.utils.dummy_pt_objects import PreTrainedModel
from .manual_template import ManualTemplate
from .manual_verbalizer import ManualVerbalizer
from .automatic_verbalizer import AutomaticVerbalizer
from .prefix_tuning_template import PrefixTuningTemplate
from .knowledgeable_verbalizer import KnowledgeableVerbalizer
from .ptuning_prompts import PtuningTemplate
from .ptr_prompts import PTRTemplate, PTRVerbalizer
from .knowledgeable_verbalizer import KnowledgeableVerbalizer
from .prefix_tuning_template import PrefixTuningTemplate
from .one2one_verbalizer import One2oneVerbalizer
from .soft_manual_prompts import SoftManualTemplate

TEMPLATE_CLASS = {
    'manual_template': ManualTemplate,
    'ptuning_template': PtuningTemplate,
    'soft_manual_template': SoftManualTemplate,
    'ptr_template': PTRTemplate,
    'prefix_tuning_template': PrefixTuningTemplate,
    #'lmbff': LMBFFTemplate
}

VERBALIZER_CLASS = {
    'manual_verbalizer': ManualVerbalizer,
    'knowledgeable_verbalizer': KnowledgeableVerbalizer,
    'automatic_verbalizer': AutomaticVerbalizer,
    'ptr_verbalizer': PTRVerbalizer,
    'one2one_verbalizer': One2oneVerbalizer
}


def load_template(config: CfgNode, 
                **kwargs,
                ):
    r"""
    Args:
        config: (:obj:`CfgNode`) The global configure file.
        kwargs: kwargs might include:
                plm_model: Optional[PreTrainedModel], 
                plm_tokenizer: Optional[PreTrainedTokenizer],
                plm_config: Optional[PreTrainedConfig]
    
    Returns:
        A template
    """
    if config.template is not None:
        template_class = TEMPLATE_CLASS[config.template]
        template = template_class.from_config(config=config[config.template], 
                                     **kwargs)
    return template

def load_verbalizer(config: CfgNode,
                **kwargs,
                ): 
    r"""
    Args:
        config: (;obj:`CfgNode`) The global configure file.
        kwargs: kwargs might include:
                plm_model: Optional[PreTrainedModel], 
                plm_tokenizer: Optional[PreTrainedTokenizer],
                plm_config: Optional[PreTrainedConfig]
    
    Returns:
        A template
    """   
    if config.verbalizer is not None:
        verbalizer_class = VERBALIZER_CLASS[config.verbalizer]
        verbalizer = verbalizer_class.from_config(config=config[config.verbalizer], 
                                     **kwargs)
    return verbalizer
