# Backend image security findings

Local Trivy report: `outputs/security/backend-remediated.json`. 44 HIGH/CRITICAL package/advisory occurrences remain. Scan failed as intended.

Removed unused curl and libcurl dependencies; image rebuilt and ten runtime checks passed. Remaining findings are not waived. No new production approval is implied.

| Advisory | Package | Installed | Listed fix |
| --- | --- | --- | --- |
| CVE-2026-76642 | bsdutils | 1:2.41.5-0+deb13u1 | None listed |
| CVE-2026-78408 | bsdutils | 1:2.41.5-0+deb13u1 | None listed |
| CVE-2026-78409 | bsdutils | 1:2.41.5-0+deb13u1 | None listed |
| CVE-2026-78410 | bsdutils | 1:2.41.5-0+deb13u1 | None listed |
| CVE-2026-54369 | libacl1 | 2.3.2-2+b1 | None listed |
| CVE-2026-76642 | libblkid1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78408 | libblkid1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78409 | libblkid1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78410 | libblkid1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-76642 | liblastlog2-2 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78408 | liblastlog2-2 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78409 | liblastlog2-2 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78410 | liblastlog2-2 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-76642 | libmount1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78408 | libmount1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78409 | libmount1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78410 | libmount1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2025-69720 | libncursesw6 | 6.5+20250216-2 | None listed |
| CVE-2026-76642 | libsmartcols1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78408 | libsmartcols1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78409 | libsmartcols1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78410 | libsmartcols1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-16742 | libsystemd0 | 257.13-1~deb13u1 | None listed |
| CVE-2025-69720 | libtinfo6 | 6.5+20250216-2 | None listed |
| CVE-2026-16742 | libudev1 | 257.13-1~deb13u1 | None listed |
| CVE-2026-76642 | libuuid1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78408 | libuuid1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78409 | libuuid1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78410 | libuuid1 | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-76642 | login | 1:4.16.0-2+really2.41.5-0+deb13u1 | None listed |
| CVE-2026-78408 | login | 1:4.16.0-2+really2.41.5-0+deb13u1 | None listed |
| CVE-2026-78409 | login | 1:4.16.0-2+really2.41.5-0+deb13u1 | None listed |
| CVE-2026-78410 | login | 1:4.16.0-2+really2.41.5-0+deb13u1 | None listed |
| CVE-2026-76642 | mount | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78408 | mount | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78409 | mount | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78410 | mount | 2.41.5-0+deb13u1 | None listed |
| CVE-2025-69720 | ncurses-base | 6.5+20250216-2 | None listed |
| CVE-2025-69720 | ncurses-bin | 6.5+20250216-2 | None listed |
| CVE-2026-9538 | perl-base | 5.40.1-6+deb13u1 | None listed |
| CVE-2026-76642 | util-linux | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78408 | util-linux | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78409 | util-linux | 2.41.5-0+deb13u1 | None listed |
| CVE-2026-78410 | util-linux | 2.41.5-0+deb13u1 | None listed |

Owner: Member 4 tracks upstream base/package fixes; team owns production release approval. Federation findings remain separately recorded in security-findings.md.
