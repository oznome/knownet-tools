import os
from ._version import version_info, __version__

from .example import *

from .featuresearch import *

def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'knownet_tools',
        'require': 'knownet_tools/extension'
    }]
