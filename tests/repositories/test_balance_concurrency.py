from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import sessionmaker

from app.models.transaction import Balance
from app.models.user import User
from app.repositories.transaction_repository import BalanceRepository


def test_concurrent_balance_updates_are_not_lost(session_engine, db):
    debtor = User(
        email="concurrent-debtor@example.com",
        full_name="Concurrent Debtor",
        hashed_password="unused",
    )
    creditor = User(
        email="concurrent-creditor@example.com",
        full_name="Concurrent Creditor",
        hashed_password="unused",
    )
    db.add_all([debtor, creditor])
    db.commit()
    debtor_id = debtor.id
    creditor_id = creditor.id
    worker_session = sessionmaker(bind=session_engine)

    def add_ten_dollars():
        with worker_session() as session:
            BalanceRepository(session).update_balance(
                user_id=debtor_id,
                owes_to_id=creditor_id,
                amount=10,
            )
            session.commit()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(add_ten_dollars) for _ in range(2)]
        for future in futures:
            future.result()

    db.expire_all()
    balances = db.query(Balance).filter(
        Balance.user_id == debtor_id,
        Balance.owes_to_id == creditor_id,
        Balance.group_id.is_(None),
        Balance.currency_code == "INR",
    ).all()
    assert len(balances) == 1
    assert float(balances[0].amount) == 20.0
