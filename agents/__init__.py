"""
FairGrade AI — Agent Package
Each module encapsulates a single agent responsibility in the pipeline.
"""

from .ocr_agent import OCRAgent
from .privacy_agent import PrivacyAgent
from .evaluation_agent import EvaluationAgent
from .bias_agent import BiasAgent
from .reporting_agent import ReportingAgent

__all__ = [
    "OCRAgent",
    "PrivacyAgent",
    "EvaluationAgent",
    "BiasAgent",
    "ReportingAgent",
]
