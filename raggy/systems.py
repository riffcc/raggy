"""System registration for RaggyNode"""
from .veracity import VeracitySystem
from .cooperation import CooperationEngine
from .reality import RealityLayer
from .cognition import CognitionEngine
from .visual import VisualProcessor
from .ollama import OllamaIntegration

def register_systems(node):
    """Register all systems with a RaggyNode"""
    node.add_system('veracity', VeracitySystem(node))
    node.add_system('cooperation', CooperationEngine(node))
    node.add_system('reality', RealityLayer(node))
    node.add_system('cognition', CognitionEngine(node))
    node.add_system('visual', VisualProcessor(node))
    node.add_system('ollama', OllamaIntegration(node))
