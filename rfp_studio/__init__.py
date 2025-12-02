# rfp_studio/__init__.py
"""RFP Studio - AI-orchestrated RFP automation platform."""

from .orchestrator.langgraph_flow import run_flow
from .config import get_settings

__version__ = "0.1.0"