from typing import List, Optional, Sequence
import math
from sc2.unit import Unit
from sc2.position import Point2
from sc2.units import Units


def position_units_in_concave(units: Sequence[Unit], center: Point2, target: Point2, radius: float = 8.0, arc_degrees: float = 180.0) -> None:
    """
    Positions units in a concave formation facing a target.
    
    Args:
        units: The units to position in the concave formation
        center: The center point of the formation (usually your army's center)
        target: The target to face (usually the enemy's position)
        radius: The radius of the concave arc
        arc_degrees: Width of the arc in degrees (180 = semicircle)
    """
    if not units:
        return
    
    # Calculate direction vector from center to target
    if center.distance_to(target) < 1.0:
        # If center and target are too close, use a default direction
        direction_x, direction_y = 1.0, 0.0
    else:
        direction = target - center
        length = direction.length
        direction_x, direction_y = direction.x / length, direction.y / length
    
    # Calculate positions along the arc
    num_units = len(units)
    positions = []
    
    # Arc angles range from -half_arc to +half_arc
    half_arc = arc_degrees / 2
    start_angle_rad = math.radians(-half_arc)
    end_angle_rad = math.radians(half_arc)
    angle_step = (end_angle_rad - start_angle_rad) / max(num_units - 1, 1)  # Avoid division by zero
    
    # Calculate positions along the arc
    for i in range(num_units):
        angle_rad = start_angle_rad + i * angle_step
        
        # Manually rotate the direction vector by the angle
        # Using rotation matrix: [cos(θ) -sin(θ); sin(θ) cos(θ)]
        sin_angle = math.sin(angle_rad)
        cos_angle = math.cos(angle_rad)
        
        # Apply rotation to original direction
        rotated_x = direction_x * cos_angle - direction_y * sin_angle
        rotated_y = direction_x * sin_angle + direction_y * cos_angle
        
        # Position on the arc
        pos_x = center.x + (rotated_x * radius)
        pos_y = center.y + (rotated_y * radius)
        positions.append(Point2((pos_x, pos_y)))
    
    # Assign each unit to the closest position
    for unit in units:
        # Find the closest unassigned position
        closest_dist = float('inf')
        closest_pos = None
        
        for pos in positions:
            dist = unit.position.distance_to(pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_pos = pos
        
        if closest_pos:
            positions.remove(closest_pos)
            unit.move(closest_pos)


class ConcaveFormationGroup:
    """
    Manages a dynamic concave formation for a group of units.
    Call update() each frame to keep units in formation.
    """
    def __init__(
        self,
        units: Sequence[Unit],
        radius: float = 8.0,
        arc_degrees: float = 180.0,
    ) -> None:
        self.units = list(units)
        self.radius = radius
        self.arc_degrees = arc_degrees
        self._last_enemy_center = None
        
    def update(self, enemy_center: Point2) -> None:
        """
        Repositions the units in a concave facing the enemy center.
        Call this every frame from the combat manager.
        """
        if not self.units:
            return
            
        # If enemy center hasn't changed much, skip reposition (optional, for efficiency)
        if self._last_enemy_center and (self._last_enemy_center - enemy_center).length < 0.5:
            return
            
        self._last_enemy_center = enemy_center
        
        # Use the position_units_in_concave utility
        # Center is the group's centroid
        group_center = self._group_center()
        position_units_in_concave(
            self.units,
            center=group_center,
            target=enemy_center,
            radius=self.radius,
            arc_degrees=self.arc_degrees
        )
        
    def _group_center(self) -> Point2:
        """Returns the centroid of the group's current positions."""
        if not self.units:
            return Point2((0, 0))
            
        x = sum(u.position.x for u in self.units) / len(self.units)
        y = sum(u.position.y for u in self.units) / len(self.units)
        return Point2((x, y))
        
    def set_units(self, units: Sequence[Unit]) -> None:
        """Updates the group's units (e.g., if squad composition changes)."""
        self.units = list(units)
        
    def set_parameters(self, radius: Optional[float] = None, arc_degrees: Optional[float] = None) -> None:
        """Dynamically update formation parameters."""
        if radius is not None:
            self.radius = radius
        if arc_degrees is not None:
            self.arc_degrees = arc_degrees