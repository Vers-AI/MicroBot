from typing import Optional

from ares.consts import UnitRole
from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.group import AMoveGroup, StutterGroupBack

from ares import AresBot
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2

import numpy as np

class MyBot(AresBot):
    BIO_TYPE: set[UnitTypeId] = {UnitTypeId.MARINE, UnitTypeId.MARAUDER}
    def __init__(self, game_step_override: Optional[int] = None):
        super().__init__(game_step_override)
    
  
    async def on_step(self, iteration: int) -> None:
        await super(MyBot, self).on_step(iteration)

        bio_force: Units = self.mediator.get_units_from_role(role=UnitRole.ATTACKING)

        if bio_force:
            self._bio_ball(bio_force, self.game_info.map_center)

    async def on_unit_created(self, unit: Unit) -> None:
        await super().on_unit_created(unit)
        if unit.type_id in self.BIO_TYPE:
            self.mediator.assign_role(
                tag=unit.tag, role=UnitRole.ATTACKING
            )
    
    def _bio_ball(self, bio_forces: Units, target: Point2) -> None:
        formation_a: CombatManeuver = CombatManeuver()
        formation_a.add(
            AMoveGroup(
                group=bio_forces,
                group_tags={r.tag for r in bio_forces},
                target=target,
            )
        )
        self.register_behavior(formation_a)
        

        


        

   