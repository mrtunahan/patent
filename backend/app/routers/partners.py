from fastapi import APIRouter

from app.core.deps import DbSession
from app.schemas import PartnerSummary
from app.services import summaries

router = APIRouter(prefix="/partners", tags=["partners"])


@router.get("", response_model=list[PartnerSummary])
def list_partners(db: DbSession):
    """Salt okunur özet: ortaklar patent kayıtlarından türetilir."""
    return summaries.partners_summary(db)
