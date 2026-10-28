from typing import Annotated

from fastapi import Depends, Path
from sqlalchemy.orm import Session

from app.database import get_db

DbSession = Annotated[Session, Depends(get_db)]

# SQLite INTEGER 64-bit'tir; bunu aşan id sürücüde OverflowError (500) üretirdi, böylece 422 döner.
SQLITE_MAX_INT = 2**63 - 1
ItemId = Annotated[int, Path(le=SQLITE_MAX_INT)]
