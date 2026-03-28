#!/usr/bin/env python3
"""Sign or verify skill packs using Ed25519.

Usage:
    # Sign all packs (requires SIGNING_PRIVATE_KEY env var)
    python scripts/sign_packs.py

    # Verify all packs (requires SIGNING_PUBLIC_KEY env var)
    python scripts/sign_packs.py --verify
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def sign_packs(packs_dir: Path) -> int:
    """Sign all .tar.gz packs with Ed25519."""
    key_b64 = os.environ.get("SIGNING_PRIVATE_KEY", "")
    if not key_b64:
        print("Error: SIGNING_PRIVATE_KEY environment variable not set", file=sys.stderr)
        return 1

    private_key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(key_b64))
    signed = 0

    for pack_file in sorted(packs_dir.glob("*.tar.gz")):
        pack_data = pack_file.read_bytes()
        digest = hashlib.sha256(pack_data).digest()
        signature = private_key.sign(digest)
        sig_b64 = base64.b64encode(signature).decode()

        sig_path = pack_file.with_suffix(pack_file.suffix + ".sig")
        sig_path.write_text(sig_b64 + "\n")

        sha_path = pack_file.with_name(pack_file.name.replace(".tar.gz", ".sha256"))
        sha_path.write_text(hashlib.sha256(pack_data).hexdigest() + "  " + pack_file.name + "\n")

        print(f"  Signed: {pack_file.name}")
        signed += 1

    print(f"\n{signed} packs signed")
    return 0


def verify_packs(packs_dir: Path) -> int:
    """Verify all signed packs."""
    key_b64 = os.environ.get("SIGNING_PUBLIC_KEY", "")
    if not key_b64:
        print("Error: SIGNING_PUBLIC_KEY environment variable not set", file=sys.stderr)
        return 1

    public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(key_b64))
    verified = 0
    failed = 0

    for pack_file in sorted(packs_dir.glob("*.tar.gz")):
        sig_path = pack_file.with_suffix(pack_file.suffix + ".sig")
        if not sig_path.exists():
            print(f"  MISSING SIG: {pack_file.name}", file=sys.stderr)
            failed += 1
            continue

        pack_data = pack_file.read_bytes()
        digest = hashlib.sha256(pack_data).digest()
        signature = base64.b64decode(sig_path.read_text().strip())

        try:
            public_key.verify(signature, digest)
            print(f"  OK: {pack_file.name}")
            verified += 1
        except Exception:
            print(f"  FAILED: {pack_file.name}", file=sys.stderr)
            failed += 1

    print(f"\n{verified} verified, {failed} failed")
    return 1 if failed > 0 else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Sign or verify skill packs")
    parser.add_argument("--verify", action="store_true", help="Verify instead of sign")
    parser.add_argument("--dir", default="packs/skills", help="Packs directory")
    args = parser.parse_args()

    toolbox_root = Path(__file__).parent.parent
    packs_dir = toolbox_root / args.dir

    if not packs_dir.exists():
        print(f"Error: directory {packs_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    if args.verify:
        sys.exit(verify_packs(packs_dir))
    else:
        sys.exit(sign_packs(packs_dir))


if __name__ == "__main__":
    main()
