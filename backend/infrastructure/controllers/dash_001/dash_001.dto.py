# dto.py
from dataclasses import dataclass


@dataclass
class PlantDTO:
    id: int
    name: str
    coordinates: list
    capacity: str
    status: str


@dataclass
class KpiDTO:
    key: int
    kpi: str
    jazla: str
    ummAlQuwain: str
    rabigh: str
    taweeiah: str
    alDur: str
    suqaia: str
