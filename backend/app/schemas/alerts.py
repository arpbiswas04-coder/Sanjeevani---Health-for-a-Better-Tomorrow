from typing import Literal
from uuid import UUID
from pydantic import Field,model_validator
from app.schemas.platform import Input


class RuleInput(Input):
    facility_id:UUID
    kind:Literal['LOW_STOCK','CRITICAL_STOCK','EXPIRY','HIGH_BED_OCCUPANCY','STAFFING_SHORTAGE','MAINTENANCE','COLD_CHAIN_EXCURSION']
    threshold:float=Field(ge=0,le=2_000_000_000)
    window_days:int=Field(90,ge=1,le=3650)
    severity:Literal['info','warning','critical']='warning'
    active:bool=True

    @model_validator(mode='after')
    def threshold_valid(self):
        if self.kind=='HIGH_BED_OCCUPANCY' and self.threshold>1:
            raise ValueError('Occupancy threshold must be between 0 and 1')
        return self


class AlertAction(Input):
    status:Literal['acknowledged','resolved']


class EscalationInput(Input):
    rule_id:UUID
    after_minutes:int=Field(ge=1,le=525600)
    recipient_id:UUID
    channel:Literal['in-app','email','sms','push']='in-app'
    active:bool=True
