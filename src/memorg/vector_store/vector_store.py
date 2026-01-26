from datetime import datetime
from typing import List, Dict, Any, Optional, Protocol

class VectorStore(Protocol):
    async def add_vector(self, id: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        ...

    async def search_nearest(self, vector: List[float], limit: int) -> List[Dict[str, Any]]:
        ...

    async def delete_vector(self, id: str) -> None:
        ...

    async def reindex(self) -> None:
        ...