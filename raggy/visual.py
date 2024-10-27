from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional
import asyncio
from PIL import Image
import numpy as np
from .node import RaggyNode

@dataclass
class VisualPattern:
    id: str
    position: Tuple[int, int]
    color: Tuple[int, int, int]
    connections: Dict[str, float] = field(default_factory=dict)

class VisualProcessor:
    def __init__(self, node: RaggyNode):
        self.node = node
        self.patterns: Dict[str, VisualPattern] = {}
        self._pattern_doc = None
        
    async def initialize(self):
        self._pattern_doc = await self.node._node.docs.create()
        
    async def process_image(self, image_data: bytes) -> List[VisualPattern]:
        # Convert bytes to PIL Image
        image = Image.open(image_data)
        # Convert to RGB array
        rgb_array = np.array(image)
        
        patterns = []
        height, width = rgb_array.shape[:2]
        
        # Extract patterns based on color similarity
        for y in range(height):
            for x in range(width):
                color = tuple(rgb_array[y, x])
                pattern_id = f"pattern_{x}_{y}"
                pattern = VisualPattern(
                    id=pattern_id,
                    position=(x, y),
                    color=color
                )
                self.patterns[pattern_id] = pattern
                patterns.append(pattern)
                
        # Form rails between patterns
        await self._form_pattern_rails(patterns)
        await self._save_patterns()
        
        return patterns
        
    async def _form_pattern_rails(self, patterns: List[VisualPattern]):
        for i, pattern1 in enumerate(patterns):
            for pattern2 in patterns[i+1:]:
                # Calculate spatial relationship
                spatial_dist = self._spatial_distance(
                    pattern1.position,
                    pattern2.position
                )
                # Calculate color similarity
                color_sim = self._color_similarity(
                    pattern1.color,
                    pattern2.color
                )
                
                # Create rail if patterns are related
                if spatial_dist < 50 or color_sim > 0.8:
                    weight = (1 - spatial_dist/100 + color_sim) / 2
                    pattern1.connections[pattern2.id] = weight
                    pattern2.connections[pattern1.id] = weight
                    
                    # Create veracity rail for pattern relationship
                    await self.node.veracity.create_rail(
                        pattern2.id,
                        semantic_closeness=weight,
                        physical_proximity=1 - spatial_dist/100
                    )
                    
    def _spatial_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
        
    def _color_similarity(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        return 1 - np.sqrt(sum((c1 - c2)**2 for c1, c2 in zip(color1, color2))) / 441.67
        
    async def _save_patterns(self):
        if self._pattern_doc:
            patterns_data = {
                k: v.__dict__ for k, v in self.patterns.items()
            }
            await self._pattern_doc.set_bytes(
                b"patterns",
                str(patterns_data).encode()
            )
