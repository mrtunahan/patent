from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Applicant, Department, Patent, PatentPartner

GENERIC = "Bu kayıt başka kayıtlarca kullanıldığı için silinemez."


def counts(db):
    db.expire_all()
    return db.query(Patent).count(), db.query(PatentPartner).count()


def test_active_patents_block_delete_with_count_in_message(client, db, make_patent):
    dept = Department(name="Gıda")
    db.add(dept)
    db.commit()
    make_patent(department_id=dept.id)
    make_patent(department_id=dept.id)
    make_patent(department_id=dept.id, deleted=True)  # silinmiş olan sayıya girmez
    r = client.delete(f"/api/departments/{dept.id}")
    assert r.status_code == 409 and r.json()["detail"] == "Bu kayıt 2 aktif patentte kullanılıyor, silinemez."
    assert counts(db)[0] == 3  # hiçbir şey silinmedi


def test_only_deleted_patents_are_purged_with_partners_then_record_deleted(client, db, make_patent):
    applicant = Applicant(full_name="Kişi")
    db.add(applicant)
    db.commit()
    gone = make_patent(applicant_id=applicant.id, deleted=True)
    gone.partners = [PatentPartner(partner_name="Ortak")]
    db.commit()
    stranger = Applicant(full_name="Başka")
    db.add(stranger)
    db.commit()
    other = make_patent(applicant_id=stranger.id)  # başka başvuru sahibinin aktif patenti dokunulmaz
    assert counts(db) == (2, 1)
    applicant_id = applicant.id
    assert client.delete(f"/api/applicants/{applicant_id}").status_code == 204
    assert counts(db) == (1, 0)
    assert db.query(Patent).one().id == other.id and db.get(Applicant, applicant_id) is None


def test_unlinked_delete_still_works(client):
    t = client.post("/api/fsmh_types", json={"name": "Bağsız", "sort_order": 9}).json()
    assert client.delete(f"/api/fsmh_types/{t['id']}").status_code == 204


def test_department_used_as_default_by_applicant_is_blocked_and_messages_combine(client, db, make_patent):
    dept = Department(name="Peyzaj")
    db.add(dept)
    db.flush()
    db.add(Applicant(full_name="A", department_id=dept.id))
    db.add(Applicant(full_name="B", department_id=dept.id))
    db.commit()
    r = client.delete(f"/api/departments/{dept.id}")
    assert r.status_code == 409
    assert r.json()["detail"] == "Bu bölüm 2 başvuru sahibinin varsayılan bölümü olarak kullanılıyor, silinemez."
    make_patent(department_id=dept.id)
    detail = client.delete(f"/api/departments/{dept.id}").json()["detail"]
    assert detail == (
        "Bu kayıt 1 aktif patentte kullanılıyor, silinemez. "
        "Bu bölüm 2 başvuru sahibinin varsayılan bölümü olarak kullanılıyor, silinemez."
    )


def test_attorney_firm_and_fsmh_type_blocked_by_active_patent(client, db, make_patent):
    from app.models import AttorneyFirm

    firm = AttorneyFirm(name="Firma")
    db.add(firm)
    db.commit()
    p = make_patent(attorney_firm_id=firm.id)
    assert client.delete(f"/api/attorney_firms/{firm.id}").json()["detail"] == "Bu kayıt 1 aktif patentte kullanılıyor, silinemez."
    assert client.delete(f"/api/fsmh_types/{p.fsmh_type_id}").json()["detail"] == "Bu kayıt 1 aktif patentte kullanılıyor, silinemez."


def test_failure_rolls_back_purge_of_deleted_patents(client, db, make_patent, monkeypatch):
    applicant = Applicant(full_name="Kişi")
    db.add(applicant)
    db.commit()
    make_patent(applicant_id=applicant.id, deleted=True).partners = [PatentPartner(partner_name="Ortak")]
    db.commit()
    real_commit = Session.commit

    def boom(self):
        raise IntegrityError("stmt", {}, Exception("fk"))

    monkeypatch.setattr(Session, "commit", boom)
    r = client.delete(f"/api/applicants/{applicant.id}")
    monkeypatch.setattr(Session, "commit", real_commit)
    assert r.status_code == 409 and r.json()["detail"] == GENERIC
    assert counts(db) == (1, 1) and db.get(Applicant, applicant.id) is not None  # silinmiş patent ve ortağı yerinde
