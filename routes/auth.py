from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import Member
from constants import CHAIRMAN_RANK, COACH_RANK, TRANSFER_COMMITTEE_RANK

auth_bp = Blueprint("auth", __name__)


def _redirect_for_rank(member: Member):
    if member.rank == CHAIRMAN_RANK:
        return redirect(url_for("chairman.dashboard"))
    if member.rank == COACH_RANK:
        return redirect(url_for("coach.dashboard"))
    if member.rank == TRANSFER_COMMITTEE_RANK:
        return redirect(url_for("transfer.portal"))
    return redirect(url_for("public.home"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_for_rank(current_user)

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        member = None
        if email and password:
            member = Member.query.filter(db.func.lower(Member.email) == email).first()

        # Intentionally generic message: never reveal whether the
        # email exists or the password was wrong - that distinction
        # helps an attacker enumerate accounts.
        if member is None or not member.check_password(password):
            flash("Invalid email or password.", "error")
            return render_template("login.html"), 401

        login_user(member)
        flash(f"Welcome back, {member.name}.", "success")
        next_url = request.args.get("next")
        # Only ever redirect to a relative path we generated ourselves,
        # never to an attacker-supplied absolute/external URL.
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return _redirect_for_rank(member)

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("public.home"))
