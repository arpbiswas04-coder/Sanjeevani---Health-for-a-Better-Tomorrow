"""Generate a separate short-lived localhost TLS identity; never overwrite."""
from datetime import datetime, timedelta, timezone
import ipaddress
import os
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID


def main():
    bundle = Path(__file__).resolve().parents[1] / 'federated/secrets/local-dev'
    if not (bundle / 'manifest.json').is_file():
        raise ValueError('Provision the restricted local bundle first')
    target = bundle / 'ingress'
    target.mkdir(mode=0o700)
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.now(timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(days=7))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'), x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), True)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), False)
        .sign(key, hashes.SHA256()))
    for filename, raw in [('cert.pem', cert.public_bytes(serialization.Encoding.PEM)),
                          ('key.pem', key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))]:
        descriptor = os.open(target / filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
    print('Separate localhost ingress certificate created; expires in seven days; no trust-store changes.')


if __name__ == '__main__':
    main()
