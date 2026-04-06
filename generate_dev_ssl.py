"""
Tạo chứng chỉ TLS tự ký (dev / LAN) cho Flask — trình duyệt sẽ cảnh báo
"không tin cậy" cho đến khi bạn thêm vào Trusted Root (tùy chọn).

Chạy một lần (hoặc khi đổi IP máy):
  python generate_dev_ssl.py
  python generate_dev_ssl.py --ip 192.168.1.100

Sau đó bật HTTPS:
  set USE_HTTPS=1
  python app.py
"""
from __future__ import annotations

import argparse
import ipaddress
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def main() -> None:
    p = argparse.ArgumentParser(description="Tạo ssl/dev.crt + ssl/dev.key (self-signed).")
    p.add_argument(
        "--ip",
        action="append",
        default=[],
        metavar="ADDR",
        help="Thêm IP vào SAN (có thể lặp). Mặc định: 127.0.0.1 và 192.168.1.230",
    )
    p.add_argument(
        "--extra-ips",
        default="192.168.1.230",
        help="Chuỗi IP cách nhau bởi dấu phẩy (mặc định: 192.168.1.230)",
    )
    args = p.parse_args()

    out_dir = Path(__file__).resolve().parent / "ssl"
    out_dir.mkdir(parents=True, exist_ok=True)
    key_path = out_dir / "dev.key"
    cert_path = out_dir / "dev.crt"

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "VN"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PhongKhamLocal"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ]
    )

    san_list: list[x509.GeneralName] = [
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        x509.IPAddress(ipaddress.IPv6Address("::1")),
    ]
    for raw in args.extra_ips.split(","):
        raw = raw.strip()
        if raw:
            san_list.append(x509.IPAddress(ipaddress.ip_address(raw)))
    for addr in args.ip:
        san_list.append(x509.IPAddress(ipaddress.ip_address(addr)))

    # Tránh trùng SAN
    seen = set()
    dedup: list[x509.GeneralName] = []
    for g in san_list:
        k = str(g.value)
        if k not in seen:
            seen.add(k)
            dedup.append(g)
    san_list = dedup

    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=825))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    print(f"OK wrote:\n  {key_path}\n  {cert_path}")
    print("SAN:", ", ".join(str(x.value) for x in san_list))


if __name__ == "__main__":
    main()
