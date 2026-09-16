'''
core data types for data delivery route planner
'''
from  dataclasses import dataclass,field
from typing import List
EPSILION=1e-9


@dataclass(frozen=True)
class Delivery:
    """_
    represents one delivery requests from imput file
    """
    id :str
    area:str
    area_key:str # normalized grouping key as small letter " nasrcity"
    priority:int
    weight:float
    seq:int # position in the input file
    
    def __str__(self)-> str:
        return f"Delivery(id={self.id}, area={self.area}, area_key={self.area_key}, priority={self.priority}, weight={self.weight}, seq={self.seq})"

@dataclass
class Trip:
    """_
    represents one trip of a delivery vehicle and never exceed  max capacity of the vehicle
    """
    capacity:float
    deliveries:List[Delivery]=field(default_factory=list)
    
    @property
    def total_weight(self)->float:
        return sum(delivery.weight for delivery in self.deliveries)
    
    @property
    def remaning(self)->float:
        return self.capacity-self.total_weight
    
    @property
    def areas(self)->List[str]:
        """_
        display names in the area of the trip  in first_seen_order of the deliveries in the trip
        """
        seen={}
        for delivery in self.deliveries:
            seen.setdefault(delivery.area_key,delivery.area)
        return list(seen.values())
    @property
    def is_mixed(self)->bool:
        """_
        check if the trip is mixed or not
        """
        return len(self.areas)>1
    @property
    def top_pirority(self)->int:
        """_
        return the hmost  urgent  pirotity of the trip  based on the deliveries in the trip
        """ 
        return min(delivery.priority for delivery in self.deliveries)
    @property
    def  utilization(self)->float:
        """_
        return the utilization of the trip based on the deliveries in the trip
        """
        return self.total_weight/self.capacity if self.capacity else 0.0
    def fits(self,delivery:Delivery)->bool:
        """_
        check if the delivery can fit in the trip or not
        """
        return self.remaning>=delivery.weight
    
    def add_delivery(self,delivery:Delivery)->None:
        if not self.fits(delivery):
            raise ValueError(f"Delivery {delivery.id} does not fit in the trip with remaining capacity {self.remaning}")
        self.deliveries.append(delivery)
        

@dataclass
class Rejected:
    """_
    represents one rejected delivery request from imput file
    """
    identifier:str
    reason:str
    
    def __str__(self)-> str:
        return f"Rejected(identifier={self.identifier}, reason={self.reason})"