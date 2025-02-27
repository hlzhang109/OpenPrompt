from math import ceil
import os
import shutil
from typing import List
import inspect
from collections import namedtuple

import torch
from yacs.config import CfgNode
import dill
from openprompt.utils.logging import logger



def round_list(l: List[float], max_sum:int):
    r"""round a list of float e.g. [0.2,1.5, 4.5]
    to [1,2,4] # ceil and restrict the sum to `max_sum`
    used into balanced truncate.
    """
    s = 0
    for idx, i in enumerate(l):
        i = ceil(i)
        if s <= max_sum:
            s += i
            if s <= max_sum:
                l[idx] = i
            else:
                l[idx] = i - (s - max_sum)
        else:
            l[idx] = int(0)
    assert sum(l) == max_sum


def signature(f):
    r"""Get the function f 's input arguments. A useful gadget
    when some function slot might be instantiated into multiple functions.
    
    Args:
        f (:obj:`function`) : the function to get the input arguments.
    
    Returns:
        namedtuple : of args, default, varargs, keywords, respectively.s

    """
    sig = inspect.signature(f)
    args = [
        p.name for p in sig.parameters.values()
        if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]
    varargs = [
        p.name for p in sig.parameters.values()
        if p.kind == inspect.Parameter.VAR_POSITIONAL
    ]
    varargs = varargs[0] if varargs else None
    keywords = [
        p.name for p in sig.parameters.values()
        if p.kind == inspect.Parameter.VAR_KEYWORD
    ]
    keywords = keywords[0] if keywords else None
    defaults = [
        p.default for p in sig.parameters.values()
        if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        and p.default is not p.empty
    ] or None
    argspec = namedtuple('Signature', ['args', 'defaults',
                                        'varargs', 'keywords'])
    return argspec(args, defaults, varargs, keywords) 

def check_config_conflicts(config: CfgNode):
    r"""check the conflicts of global config.
    """
    if config.task == "generation":
        assert config['train'].teacher_forcing == True, "You should use teacher forcing to train generation!"
    
    if config.task == "generation":
        if  config.dataloader.max_seq_length >= config.generation.max_length:
            logger.warning("In generation, your config.generation.max_length is shorter than config.max_seq_length"
                "This can lead to unexpected behavior. You should consider increasing ``config.generation.max_length``."
            )
            raise RuntimeError

def save_checkpoint(state_dict, is_best, save_path, filename='checkpoint.pt'):
    r"""save the checkpoint to :obj:`save_path`.
    """
    full_file_path= os.path.join(save_path, filename)
    logger.info("Saving the lastest checkpoint.")
    torch.save(state_dict, full_file_path, pickle_module=dill)
    if is_best:
        full_best_path= os.path.join(save_path, 'best.'+filename)
        logger.info("Saving the best checkpoint.")
        shutil.copyfile(full_file_path, full_best_path)
            
def load_checkpoint(load_path, load_best, filename="checkpoint.pt", map_location=None):
    r"""load the checkpoint from :obj:`load_path`.
    """
    if load_best:
        full_file_path= os.path.join(load_path, "best."+filename)
        logger.info("Loading the best checkpoint.")
    else:
        full_file_path= os.path.join(load_path, filename)
        logger.info("Loading the latest checkpoint.")
    state_dict = torch.load(full_file_path,pickle_module=dill, map_location=map_location)
    return state_dict



