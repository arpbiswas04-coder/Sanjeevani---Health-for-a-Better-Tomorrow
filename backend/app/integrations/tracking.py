from typing import Protocol
from pydantic import BaseModel,Field,AwareDatetime


class TrackingObservation(BaseModel):
    vehicle_id:str=Field(min_length=1,max_length=80)
    latitude:float=Field(ge=-90,le=90)
    longitude:float=Field(ge=-180,le=180)
    observed_at:AwareDatetime
    source:str=Field(min_length=1,max_length=100)


class VehicleTrackingProvider(Protocol):
    async def latest(self,vehicle_id:str)->TrackingObservation:
        """Return actual timestamped provider data; do not synthesize GPS positions."""
        ...
