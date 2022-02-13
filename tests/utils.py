def commit(db, o):
    db.session.add(o)
    db.session.commit()
