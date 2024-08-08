from dataclasses import dataclass

@dataclass
class GameStub:
    title: str = ''
    bgg_id: int = 0
    owned: bool = True
