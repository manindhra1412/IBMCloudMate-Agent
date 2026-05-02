# from .cloudant import tools as cloudant_tools

from .cloudant_tools import cloudant_tools
from .cos_tools import cos_tools

# Combine all tools
all_tools = cloudant_tools + cos_tools

__all__ = ['all_tools', 'cloudant_tools', 'cos_tools'] 