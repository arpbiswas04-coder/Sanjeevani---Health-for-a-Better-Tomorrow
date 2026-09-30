"""Fixed-roster pairwise masking demonstration, not production SecAgg+.

All participants are required. Public-key/roster authenticity must be supplied
by a trusted harness; this layer does not authenticate its own key exchange.
"""
import hashlib
import json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from federated.privacy.gaussian import vector
from optimization.common.validation import ValidationError, identifier, object_fields

MODULUS = 2 ** 128
SCALE = 1_000_000


def transcript(public_keys, nonce):
    if not isinstance(public_keys, dict) or not 3 <= len(public_keys) <= 100:
        raise ValidationError("Masking requires a fixed roster of 3..100 nodes")
    identifier(nonce, "round nonce")
    for node, key in public_keys.items():
        identifier(node, "node")
        if not isinstance(key, bytes) or len(key) != 32:
            raise ValidationError("Invalid public key")
    if len(set(public_keys.values())) != len(public_keys): raise ValidationError("Duplicate public key")
    value = {"protocol": "masked-sum-v1", "nonce": nonce,
             "keys": {node: key.hex() for node, key in sorted(public_keys.items())}}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).digest()


class MaskingClient:
    def __init__(self, node):
        self.node = identifier(node, "node")
        self._private = X25519PrivateKey.generate()
        self.public = self._private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self._used = False

    def mask(self, values, public_keys, nonce):
        values = vector(values)
        digest = transcript(public_keys, nonce)
        if self._used or public_keys.get(self.node) != self.public:
            raise ValidationError("Masking key reused or identity mismatch")
        self._used = True  # Fresh ephemeral keys for every round, including aborts.
        encoded = [round(x * SCALE) % MODULUS for x in values]
        for peer, public in sorted(public_keys.items()):
            if peer == self.node: continue
            shared = self._private.exchange(X25519PublicKey.from_public_bytes(public))
            pair = json.dumps(sorted([peer, self.node])).encode()
            stream = HKDF(algorithm=hashes.SHA256(), length=32, salt=digest,
                          info=b"sanjeevani-pair-mask-v1:" + pair).derive(shared)
            sign = 1 if self.node < peer else -1
            for index in range(2):
                mask = int.from_bytes(stream[index * 16:(index + 1) * 16], "big")
                encoded[index] = (encoded[index] + sign * mask) % MODULUS
        return {"node_id": self.node, "transcript": digest.hex(), "masked": encoded}


def aggregate(packets, public_keys, nonce):
    digest = transcript(public_keys, nonce).hex()
    if not isinstance(packets, list) or len(packets) != len(public_keys):
        raise ValidationError("Dropout: all participants are required; abort the round")
    seen, total = set(), [0, 0]
    for packet in packets:
        row = object_fields(packet, required={"node_id", "transcript", "masked"}, optional=set(), path="masked update")
        node = identifier(row["node_id"], "node_id")
        if node not in public_keys or node in seen or row["transcript"] != digest:
            raise ValidationError("Duplicate/unknown participant or stale transcript")
        seen.add(node)
        if not isinstance(row["masked"], list) or len(row["masked"]) != 2 or any(type(x) is not int or not 0 <= x < MODULUS for x in row["masked"]):
            raise ValidationError("Malformed masked vector")
        total = [(a + b) % MODULUS for a, b in zip(total, row["masked"])]
    signed = [x - MODULUS if x >= MODULUS // 2 else x for x in total]
    if any(abs(x) > len(public_keys) * 1_000_000 * SCALE for x in signed):
        raise ValidationError("Aggregate outside supported bounds")
    return [x / SCALE / len(public_keys) for x in signed]
