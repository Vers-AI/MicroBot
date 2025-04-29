from typing import TYPE_CHECKING, List
from sc2.units import Units
from sc2.position import Point2
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit

from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.group import AMoveGroup, StutterGroupBack
from ares.behaviors.combat.individual import StutterUnitBack, AMove
from ares.managers.squad_manager import UnitSquad
from ares.consts import UnitRole, UnitTreeQueryType

import numpy as np
from cython_extensions import cy_center, cy_pick_enemy_target, cy_closest_to

# Import the formation logic
from .formations import ConcaveFormationGroup

if TYPE_CHECKING:
    from ares import AresBot

def core_army(bot: "AresBot", forces: Units, target: Point2) -> None:
    """
    Controls a group of units - moves as a ball if no enemies are visible,
    otherwise uses squad-based micro for Marines and Marauders, and individual micro for other units.
    """
    grid: np.ndarray = bot.mediator.get_ground_grid
    enemy_units = bot.enemy_units
    
    # Filter out Marines and Marauders
    marines = forces.filter(lambda u: u.type_id == UnitTypeId.MARINE)
    marauders = forces.filter(lambda u: u.type_id == UnitTypeId.MARAUDER)
    bio_units = marines + marauders
    other_units = forces.filter(lambda u: u.type_id not in [UnitTypeId.MARINE, UnitTypeId.MARAUDER])
    
    if not enemy_units:
        # No enemies visible - move as a group without squad formation
        group_formation: CombatManeuver = CombatManeuver()
        group_formation.add(
            AMoveGroup(
                group=forces,
                group_tags={unit.tag for unit in forces},
                target=target,
            )
        )
        bot.register_behavior(group_formation)
    
    else:
        # Enemies detected - use squad-based micro for bio units
        if bio_units:
            # Get bio squads (using spatial grouping)
            bio_squads: list[UnitSquad] = bot.mediator.get_squads(
                role=UnitRole.ATTACKING,  # Using ATTACKING role that's set in main.py
                unit_type=[UnitTypeId.MARINE, UnitTypeId.MARAUDER],
                squad_radius=10.0  # Marines and Marauders within 7 range form a squad
            )
            
            # Control each bio squad
            for squad in bio_squads:
                squad_position = squad.squad_position
                squad_units = squad.squad_units
                squad_tags = squad.tags
                
                # Find enemies near this squad
                nearby_enemies: Units = bot.mediator.get_units_in_range(
                    start_points=[squad_position],
                    distances=15.0,  # Detect enemies within 11 range of squad center
                    query_tree=UnitTreeQueryType.EnemyGround,
                )[0]
                
                # Create combat maneuver for this squad
                squad_maneuver: CombatManeuver = CombatManeuver()
                
                # Determine if we should form a concave or do direct combat
                safe_distance = 15.0  # Distance where we consider it's safe to form a concave
                closest_enemy_distance = 999
                if nearby_enemies:
                    # Find the distance to the closest enemy unit
                    for enemy in nearby_enemies:
                        dist = squad_position.distance_to(enemy.position)
                        if dist < closest_enemy_distance:
                            closest_enemy_distance = dist
                
                # If enemies are nearby but at a safe distance, form a concave
                if nearby_enemies and closest_enemy_distance > safe_distance:
                    # Calculate enemy center for the concave formation
                    enemy_center_tuple = cy_center(nearby_enemies)
                    enemy_center = Point2(enemy_center_tuple)  # Convert tuple to Point2

                    # Use ConcaveFormationGroup for dynamic formation
                    # TODO fix the implementation, because formations.py isn't set as an ARES combat behavior
                    concave_group = ConcaveFormationGroup(
                        units=squad_units,
                        radius=10.0,
                        arc_degrees=120.0
                    )
                    concave_group.update(enemy_center)

                    # Create a combat maneuver for after the formation is set
                    concave_maneuver = CombatManeuver()
                    concave_maneuver.add(
                        AMoveGroup(
                            group=squad_units,
                            group_tags=squad_tags,
                            target=enemy_center
                        )
                    )
                    bot.register_behavior(concave_maneuver)
                    continue
                
                # If enemies are too close or concave wasn't created, attack, when low health StutterUnitBack
                if nearby_enemies:
                    # Add the stutter back behavior at highest priority
                    for unit in squad_units:
                        formation= CombatManeuver()
                        closest_enemy = cy_closest_to(unit.position, enemy_units)
                        # TODO change health percentage to if its being targeted 
                        if unit.health_percentage < 1:
                            formation.add(
                                StutterUnitBack(
                                    unit=unit,
                                    target=closest_enemy,
                                    grid=grid
                                )
                            )
                        else:
                            formation.add(
                                AMove(
                                    unit=unit,
                                    target=closest_enemy
                                )
                            )
                        bot.register_behavior(formation)
                
                # Fallback behavior: A-move to target
                squad_maneuver.add(
                    AMoveGroup(
                        group=squad_units,
                        group_tags=squad_tags,
                        target=target
                    )
                )
                
                bot.register_behavior(squad_maneuver)
        
        # Individual micro for other units
        for unit in other_units:
            formation: CombatManeuver = CombatManeuver()
            try:
                # Try to use cython extension for performance
                closest_enemy = cy_closest_to(unit.position, enemy_units)
            except Exception:
                # Fallback to standard Python if cython extension fails
                closest_enemy = min(enemy_units, key=lambda e: unit.distance_to(e))
            # TODO change health percentage to if its being targeted
            if unit.health_percentage < 1:
                formation.add(StutterUnitBack(unit, closest_enemy, grid=grid))
            else:
                formation.add(AMove(unit, closest_enemy))
            
            bot.register_behavior(formation)