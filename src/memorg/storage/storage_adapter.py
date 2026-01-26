from typing import List, Dict, Any, Optional, Protocol
import logging

class StorageAdapter(Protocol):
    async def write(self, collection: str, id: str, data: Any) -> None:
        ...

    async def read(self, collection: str, id: str) -> Any:
        ...

    async def query(self, collection: str, filter: Dict[str, Any]) -> List[Any]:
        ...

    async def delete(self, collection: str, id: str) -> None:
        ...
