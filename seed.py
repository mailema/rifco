"""
One-time bootstrap script.

Every other Member account is created BY the Chairman from inside the
Chairman Portal - but the very first Chairman account has to come
from somewhere. Run this once against a fresh database:

    python seed.py

It will refuse to run if a Chairman already exists, so it is safe to
leave in the repository and re-run accidentally.

It asks for the password interactively (never pass it as a command
line argument or hard-code it - both leak into shell history / logs).
"""

import getpass

from app import create_app
from extensions import db
from models import Member
from constants import CHAIRMAN_RANK


def main():
    app = create_app()
    with app.app_context():
        existing = Member.query.filter_by(rank=CHAIRMAN_RANK).first()
        if existing:
            print(f"A Chairman already exists ({existing.email}). Nothing to do.")
            return

        print("No Chairman account found. Let's create the first one.\n")
        name = input("Full name: ").strip()
        email = input("Email: ").strip().lower()
        member_id = input("Member ID: ").strip()
        phone = input("Phone: ").strip()
        address = input("Address: ").strip()

        while True:
            password = getpass.getpass("Password (min 8 characters): ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Passwords did not match - try again.\n")
                continue
            if len(password) < 8:
                print("Password must be at least 8 characters - try again.\n")
                continue
            break

        chairman = Member(
            name=name, email=email, member_id=member_id, phone=phone,
            address=address, rank=CHAIRMAN_RANK, team_id=None,
        )
        chairman.set_password(password)
        db.session.add(chairman)
        db.session.commit()
        print(f"\nChairman account created for {name} ({email}). You can now log in.")


if __name__ == "__main__":
    main()
