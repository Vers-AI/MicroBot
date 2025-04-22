from typing import TYPE_CHECKING
from sc2.units import Units
from sc2.position import Point2
from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.group import AMoveGroup
from ares.behaviors.combat.individual import StutterUnitBack
from ares.managers.squad_manager import UnitSquad
from ares.consts import UnitRole


from cython_extensions import cy_center, cy_pick_enemy_target, cy_closest_to

import numpy as np

if TYPE_CHECKING:
    from ares import AresBot

def core_army(bot: "AresBot", forces: Units, target: Point2) -> None:
    """
    Controls a group of units - moves as a ball if no enemies are visible,
    otherwise uses individual micro behavior for combat.
    """
    grid: np.ndarray = bot.mediator.get_ground_grid
    enemy_units = bot.enemy_units

    
    
    if not enemy_units:
        # No enemies visible - move as a group
        group_formation: CombatManeuver = CombatManeuver()
        group_formation.add(
            AMoveGroup(
                group=forces,
                group_tags={r.tag for r in forces},
                target=target,
            )
        )
        bot.register_behavior(group_formation)
    
    else:
        # Enemies detected - individual micro for each unit

        for unit in forces:
            formation: CombatManeuver = CombatManeuver()
            if enemy_units:
                try:
                    # Try to use cython extension for performance
                    closest_enemy = cy_closest_to(unit.position, enemy_units)
                except Exception:
                    # Fallback to standard Python if cython extension fails
                    closest_enemy = min(enemy_units, key=lambda e: unit.distance_to(e))
                
                # Add individual micro behavior for this unit
                formation.add(StutterUnitBack(unit, closest_enemy, grid=grid))
    
            bot.register_behavior(formation)