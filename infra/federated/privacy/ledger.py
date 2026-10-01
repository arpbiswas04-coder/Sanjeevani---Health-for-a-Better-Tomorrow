"""Durable synthetic-demo release counters; not rollback-resistant storage."""
import json
import os
from pathlib import Path
import sqlite3
from contextlib import closing
from optimization.common.validation import ValidationError


class PrivacyLedger:
    def __init__(self, path, policy, nodes, *, initialize=False):
        self.path = Path(path)
        self.policy = json.dumps(policy, sort_keys=True, allow_nan=False)
        self.nodes = sorted(nodes)
        if len(self.nodes) < 3 or len(set(self.nodes)) != len(self.nodes):
            raise ValidationError("Ledger requires a distinct fixed roster")
        if self.path.is_symlink(): raise ValidationError("Symlink ledger refused")
        if initialize:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
            with closing(self.connect()) as db, db:
                db.execute("CREATE TABLE policy(value TEXT NOT NULL)")
                db.execute("INSERT INTO policy VALUES (?)", (self.policy,))
                db.execute("CREATE TABLE releases(node TEXT PRIMARY KEY,count INTEGER NOT NULL CHECK(count>=0))")
                db.executemany("INSERT INTO releases VALUES (?,0)", [(node,) for node in self.nodes])
        self.snapshot()  # Missing/corrupt/mismatched ledgers never silently reset.

    def connect(self):
        db = sqlite3.connect(self.path.resolve().as_uri() + "?mode=rw", uri=True, timeout=5)
        db.execute("PRAGMA synchronous=FULL")
        return db

    def validate(self, db):
        if db.execute("SELECT value FROM policy").fetchall() != [(self.policy,)]:
            raise ValidationError("Ledger privacy policy changed")
        rows = db.execute("SELECT node,count FROM releases ORDER BY node").fetchall()
        if [row[0] for row in rows] != self.nodes or any(type(row[1]) is not int or row[1] < 0 for row in rows):
            raise ValidationError("Ledger roster/counts invalid")
        return dict(rows)

    def snapshot(self):
        db = self.connect()
        try: return self.validate(db)
        finally: db.close()

    def reserve(self, node, budget, maximum):
        db = self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            counts = self.validate(db)
            if node not in counts: raise ValidationError("Unknown ledger participant")
            count = counts[node] + 1
            if budget(count)["epsilon"] > maximum:
                raise ValidationError("Persistent privacy budget exhausted")
            db.execute("UPDATE releases SET count=? WHERE node=?", (count, node))
            db.commit()  # Charge durably before generating or returning a release.
            return count
        finally:
            db.close()  # Uncommitted transactions roll back; committed charges remain.
