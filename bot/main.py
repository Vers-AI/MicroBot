from typing import Optional

from ares.consts import UnitRole
from ares.managers.manager_mediator import ManagerMediator

from ares import AresBot
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units

import numpy as np
from .managers.combat import core_army


class Overclock(AresBot):
    BIO_TYPE: set[UnitTypeId] = {UnitTypeId.MARINE, UnitTypeId.MARAUDER, UnitTypeId.GHOST, UnitTypeId.REAPER}
    MECH_TYPE: set[UnitTypeId] = {UnitTypeId.HELLION, UnitTypeId.SIEGETANK, UnitTypeId.CYCLONE, UnitTypeId.SCV}
    SUPPORT_TYPE: set[UnitTypeId] = {UnitTypeId.MEDIVAC, UnitTypeId.RAVEN}
    def __init__(self, game_step_override: Optional[int] = None):
        super().__init__(game_step_override)
    
    async def on_step(self, iteration: int) -> None:
        await super(Overclock, self).on_step(iteration)
        

        bio_force: Units = self.mediator.get_units_from_role(role=UnitRole.ATTACKING)

        if bio_force:
            core_army(self, bio_force, self.game_info.map_center)

    async def on_unit_created(self, unit: Unit) -> None:
        await super(Overclock, self).on_unit_created(unit)
        if unit.type_id in self.BIO_TYPE:
            self.mediator.assign_role(
                tag=unit.tag, role=UnitRole.ATTACKING
            )
        elif unit.type_id in self.MECH_TYPE:
            self.mediator.assign_role(
                tag=unit.tag, role=UnitRole.ATTACKING
            )
        elif unit.type_id in self.SUPPORT_TYPE:
            self.mediator.assign_role(
                tag=unit.tag, role=UnitRole.CONTROL_GROUP_ONE
            )
   