"""Cyan Eclipse Routeseal - metering journal (ETO-44).

ACT/SCA journal pattern: append-only JSONL, hash-chained. Every
metering record carries its sequence, the SHA-256 of its canonical
payload, the previous receipt hash, and its own receipt hash over
(seq, ts, kind, subject, payload_digest, prev). Verification
recomputes the whole chain from the file; any altered record fails
verification at its sequence. One record is written per priced op
that meters under the product's existing metering classes (PC-8:
one per dispatch seal with verdict AS-DECLARED or DEVIATION;
$0.25/op, fixture scope - records are counts, never charges).
This journal is separate from the seal receipt journal: it never
feeds record seals or verdicts, and the seal store's tamper
behaviour is unchanged.
"""
import hashlib
import json
import os
from datetime import datetime, timezone

GENESIS = "0" * 64
KIND = "metering_op"


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class MeteringJournal:
    def __init__(self, path):
        self.path = path
        d = os.path.dirname(os.path.abspath(path))
        os.makedirs(d, exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write("")
        self._load_head()

    def _load_head(self):
        self.seq = 0
        self.head = GENESIS
        for rec in self.read_all():
            self.seq = rec["seq"]
            self.head = rec["hash"]

    def read_all(self):
        out = []
        if not os.path.exists(self.path):
            return out
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def append(self, subject, payload):
        seq = self.seq + 1
        payload_digest = _sha(_canon(payload))
        body = {"seq": seq, "ts": utcnow(), "kind": KIND,
                "subject": subject, "payload": payload,
                "payload_digest": payload_digest, "prev": self.head}
        body["hash"] = _sha(_canon({k: body[k] for k in
                                    ("seq", "ts", "kind", "subject",
                                     "payload_digest", "prev")}))
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(body, sort_keys=True,
                               ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self.seq = seq
        self.head = body["hash"]
        return body

    def verify(self):
        prev = GENESIS
        expect = 1
        for rec in self.read_all():
            if rec["seq"] != expect:
                return {"ok": False, "failed_at": expect,
                        "reason": "sequence_gap"}
            if rec["prev"] != prev:
                return {"ok": False, "failed_at": rec["seq"],
                        "reason": "prev_mismatch"}
            if rec["payload_digest"] != _sha(_canon(rec["payload"])):
                return {"ok": False, "failed_at": rec["seq"],
                        "reason": "payload_digest_mismatch"}
            h = _sha(_canon({k: rec[k] for k in
                             ("seq", "ts", "kind", "subject",
                              "payload_digest", "prev")}))
            if h != rec["hash"]:
                return {"ok": False, "failed_at": rec["seq"],
                        "reason": "receipt_hash_mismatch"}
            prev = rec["hash"]
            expect += 1
        return {"ok": True, "receipts": expect - 1, "head": prev}

    def counts_by_op(self):
        counts = {}
        for rec in self.read_all():
            op = rec["payload"].get("op")
            counts[op] = counts.get(op, 0) + 1
        return counts
