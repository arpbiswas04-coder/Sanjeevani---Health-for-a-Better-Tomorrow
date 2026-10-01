# Remaining security findings

Trivy 0.74.0; report `outputs/security/federation-image.json`; 2026-09-30T13:15:09.959485803Z.

47 HIGH/CRITICAL package/advisory occurrences remain; scan exits nonzero.
No exception or production approval is implied; one CVE can affect multiple packages.

| Advisory | Installed packages | Listed fix | Owner |
| --- | --- | --- | --- |
| CVE-2025-69720 | libncursesw6 6.5+20250216-2, libtinfo6 6.5+20250216-2, ncurses-base 6.5+20250216-2, ncurses-bin 6.5+20250216-2 | No listed fix | Debian base maintainers / Member 4 review |
| CVE-2026-16742 | libsystemd0 257.13-1~deb13u1, libudev1 257.13-1~deb13u1 | No listed fix | Debian base maintainers / Member 4 review |
| CVE-2026-54369 | libacl1 2.3.2-2+b1 | No listed fix | Debian base maintainers / Member 4 review |
| CVE-2026-69247 | cryptography 46.0.7 | 50.0.0 | Flower maintainers / Member 4 compatibility review |
| CVE-2026-69249 | cryptography 46.0.7 | 49.0.0 | Flower maintainers / Member 4 compatibility review |
| CVE-2026-76642 | bsdutils 1:2.41.5-0+deb13u1, libblkid1 2.41.5-0+deb13u1, liblastlog2-2 2.41.5-0+deb13u1, libmount1 2.41.5-0+deb13u1, libsmartcols1 2.41.5-0+deb13u1, libuuid1 2.41.5-0+deb13u1, login 1:4.16.0-2+really2.41.5-0+deb13u1, mount 2.41.5-0+deb13u1, util-linux 2.41.5-0+deb13u1 | No listed fix | Debian base maintainers / Member 4 review |
| CVE-2026-78408 | bsdutils 1:2.41.5-0+deb13u1, libblkid1 2.41.5-0+deb13u1, liblastlog2-2 2.41.5-0+deb13u1, libmount1 2.41.5-0+deb13u1, libsmartcols1 2.41.5-0+deb13u1, libuuid1 2.41.5-0+deb13u1, login 1:4.16.0-2+really2.41.5-0+deb13u1, mount 2.41.5-0+deb13u1, util-linux 2.41.5-0+deb13u1 | No listed fix | Debian base maintainers / Member 4 review |
| CVE-2026-78409 | bsdutils 1:2.41.5-0+deb13u1, libblkid1 2.41.5-0+deb13u1, liblastlog2-2 2.41.5-0+deb13u1, libmount1 2.41.5-0+deb13u1, libsmartcols1 2.41.5-0+deb13u1, libuuid1 2.41.5-0+deb13u1, login 1:4.16.0-2+really2.41.5-0+deb13u1, mount 2.41.5-0+deb13u1, util-linux 2.41.5-0+deb13u1 | No listed fix | Debian base maintainers / Member 4 review |
| CVE-2026-78410 | bsdutils 1:2.41.5-0+deb13u1, libblkid1 2.41.5-0+deb13u1, liblastlog2-2 2.41.5-0+deb13u1, libmount1 2.41.5-0+deb13u1, libsmartcols1 2.41.5-0+deb13u1, libuuid1 2.41.5-0+deb13u1, login 1:4.16.0-2+really2.41.5-0+deb13u1, mount 2.41.5-0+deb13u1, util-linux 2.41.5-0+deb13u1 | No listed fix | Debian base maintainers / Member 4 review |
| CVE-2026-9538 | perl-base 5.40.1-6+deb13u1 | No listed fix | Debian base maintainers / Member 4 review |
| GHSA-537c-gmf6-5ccf | cryptography 46.0.7 | 48.0.1 | Flower maintainers / Member 4 compatibility review |

Cryptography fixes exceed Flower 1.39.0's `<47` constraint. Do not force incompatible versions or suppress findings. Debian received available upgrades; no listed fixes remain for these advisories. Alternative base migration requires a separately tested supported runtime.

Resolved: pip-vendored msgpack 1.1.2 and setuptools 70.3.0 records disappeared after runtime pip/bootstrap removal. Top-level setuptools 84.0.0 remains; training passed.
