from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import or_

from extensions import db
from models import Member, Team, League, Player, Transfer, SystemSetting
from constants import MEMBER_RANKS, CHAIRMAN_RANK, COACH_RANK
from routes.decorators import chairman_required

chairman_bp = Blueprint("chairman", __name__, url_prefix="/chairman")


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------
@chairman_bp.route("/")
@chairman_required
def dashboard():
    stats = {
        "members": Member.query.count(),
        "teams": Team.query.count(),
        "leagues": League.query.count(),
        "players": Player.query.count(),
        "transfers": Transfer.query.count(),
    }
    settings = SystemSetting.get_current()
    recent_transfers = (
        Transfer.query.order_by(Transfer.transferred_at.desc()).limit(5).all()
    )
    return render_template(
        "chairman/dashboard.html", stats=stats, settings=settings,
        recent_transfers=recent_transfers,
    )


# ---------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------
@chairman_bp.route("/members")
@chairman_required
def members():
    q = (request.args.get("q") or "").strip()
    query = Member.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(Member.name.ilike(like), Member.member_id.ilike(like),
                Member.email.ilike(like))
        )
    all_members = query.order_by(Member.name).all()
    return render_template("chairman/members.html", members=all_members, q=q)


@chairman_bp.route("/members/register", methods=["GET", "POST"])
@chairman_required
def register_member():
    teams = Team.query.order_by(Team.team_name).all()

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        member_id = (request.form.get("member_id") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        address = (request.form.get("address") or "").strip()
        rank = (request.form.get("rank") or "").strip()
        password = request.form.get("password") or ""
        team_id = request.form.get("team_id") or None

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        if not member_id:
            errors.append("Member ID is required.")
        if not phone:
            errors.append("Phone is required.")
        if not address:
            errors.append("Address is required.")
        if rank not in MEMBER_RANKS:
            errors.append("A valid rank must be selected.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")

        team = None
        if rank == COACH_RANK:
            if not team_id:
                errors.append("A team must be selected for a Coach.")
            else:
                team = Team.query.get(team_id)
                if team is None:
                    errors.append("Selected team does not exist.")
        else:
            # Business rule: non-coach members do not carry a team.
            team_id = None

        if not errors and Member.query.filter(db.func.lower(Member.email) == email).first():
            errors.append("A member with this email already exists.")
        if not errors and Member.query.filter_by(member_id=member_id).first():
            errors.append("A member with this Member ID already exists.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "chairman/member_form.html", teams=teams, ranks=MEMBER_RANKS,
                form=request.form, mode="create",
            )

        new_member = Member(
            name=name, email=email, member_id=member_id, phone=phone,
            address=address, rank=rank, team_id=team.id if team else None,
        )
        new_member.set_password(password)
        db.session.add(new_member)
        db.session.commit()
        flash(f"{name} registered successfully as {rank}.", "success")
        return redirect(url_for("chairman.members"))

    return render_template(
        "chairman/member_form.html", teams=teams, ranks=MEMBER_RANKS,
        form={}, mode="create",
    )


@chairman_bp.route("/members/<int:member_id>")
@chairman_required
def member_detail(member_id):
    member = Member.query.get_or_404(member_id)
    return render_template("chairman/member_detail.html", member=member)


@chairman_bp.route("/members/<int:member_id>/edit", methods=["GET", "POST"])
@chairman_required
def update_member(member_id):
    member = Member.query.get_or_404(member_id)
    teams = Team.query.order_by(Team.team_name).all()

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        phone = (request.form.get("phone") or "").strip()
        address = (request.form.get("address") or "").strip()
        rank = (request.form.get("rank") or "").strip()
        team_id = request.form.get("team_id") or None

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        if not phone:
            errors.append("Phone is required.")
        if not address:
            errors.append("Address is required.")
        if rank not in MEMBER_RANKS:
            errors.append("A valid rank must be selected.")

        existing = Member.query.filter(db.func.lower(Member.email) == email).first()
        if existing and existing.id != member.id:
            errors.append("Another member already uses that email.")

        team = None
        if rank == COACH_RANK:
            if not team_id:
                errors.append("A team must be selected for a Coach.")
            else:
                team = Team.query.get(team_id)
                if team is None:
                    errors.append("Selected team does not exist.")
        else:
            team_id = None

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "chairman/member_form.html", teams=teams, ranks=MEMBER_RANKS,
                form=request.form, mode="edit", member=member,
            )

        member.name = name
        member.email = email
        member.phone = phone
        member.address = address
        member.rank = rank
        member.team_id = team.id if team else None
        db.session.commit()
        flash("Member updated successfully.", "success")
        return redirect(url_for("chairman.member_detail", member_id=member.id))

    return render_template(
        "chairman/member_form.html", teams=teams, ranks=MEMBER_RANKS,
        form=member.__dict__, mode="edit", member=member,
    )


# ---------------------------------------------------------------------
# Leagues
# ---------------------------------------------------------------------
@chairman_bp.route("/leagues")
@chairman_required
def leagues():
    all_leagues = League.query.order_by(League.name).all()
    return render_template("chairman/leagues.html", leagues=all_leagues)


@chairman_bp.route("/leagues/create", methods=["GET", "POST"])
@chairman_required
def create_league():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("League name is required.", "error")
        elif League.query.filter(db.func.lower(League.name) == name.lower()).first():
            flash("A league with this name already exists.", "error")
        else:
            db.session.add(League(name=name))
            db.session.commit()
            flash(f"League '{name}' created.", "success")
            return redirect(url_for("chairman.leagues"))
    return render_template("chairman/league_form.html")


@chairman_bp.route("/leagues/<int:league_id>")
@chairman_required
def league_detail(league_id):
    league = League.query.get_or_404(league_id)
    return render_template("chairman/league_detail.html", league=league)


@chairman_bp.route("/leagues/<int:league_id>/delete", methods=["POST"])
@chairman_required
def delete_league(league_id):
    league = League.query.get_or_404(league_id)
    if league.teams:
        flash(
            "This league still has teams assigned to it. "
            "Reassign or remove those teams before deleting the league.",
            "error",
        )
        return redirect(url_for("chairman.league_detail", league_id=league.id))
    db.session.delete(league)
    db.session.commit()
    flash("League deleted.", "success")
    return redirect(url_for("chairman.leagues"))


# ---------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------
@chairman_bp.route("/teams")
@chairman_required
def teams():
    q = (request.args.get("q") or "").strip()
    query = Team.query
    if q:
        query = query.filter(Team.team_name.ilike(f"%{q}%"))
    all_teams = query.order_by(Team.team_name).all()
    return render_template("chairman/teams.html", teams=all_teams, q=q)


@chairman_bp.route("/teams/create", methods=["GET", "POST"])
@chairman_required
def create_team():
    all_leagues = League.query.order_by(League.name).all()

    if request.method == "POST":
        team_name = (request.form.get("team_name") or "").strip()
        league_id = request.form.get("league_id")

        errors = []
        if not team_name:
            errors.append("Team name is required.")
        elif Team.query.filter(db.func.lower(Team.team_name) == team_name.lower()).first():
            errors.append("A team with this name already exists.")

        league = League.query.get(league_id) if league_id else None
        if league is None:
            errors.append("A valid league must be selected.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "chairman/team_form.html", leagues=all_leagues, form=request.form,
                mode="create",
            )

        team = Team(team_name=team_name, league_id=league.id)
        db.session.add(team)
        db.session.commit()
        flash(f"Team '{team_name}' created in {league.name}.", "success")
        return redirect(url_for("chairman.teams"))

    return render_template(
        "chairman/team_form.html", leagues=all_leagues, form={}, mode="create",
    )


@chairman_bp.route("/teams/<int:team_id>")
@chairman_required
def team_detail(team_id):
    team = Team.query.get_or_404(team_id)
    return render_template("chairman/team_detail.html", team=team)


@chairman_bp.route("/teams/<int:team_id>/edit", methods=["GET", "POST"])
@chairman_required
def update_team(team_id):
    team = Team.query.get_or_404(team_id)
    all_leagues = League.query.order_by(League.name).all()

    if request.method == "POST":
        team_name = (request.form.get("team_name") or "").strip()
        league_id = request.form.get("league_id")

        errors = []
        if not team_name:
            errors.append("Team name is required.")
        existing = Team.query.filter(db.func.lower(Team.team_name) == team_name.lower()).first()
        if existing and existing.id != team.id:
            errors.append("Another team already uses that name.")

        league = League.query.get(league_id) if league_id else None
        if league is None:
            errors.append("A valid league must be selected.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "chairman/team_form.html", leagues=all_leagues, form=request.form,
                mode="edit", team=team,
            )

        team.team_name = team_name
        team.league_id = league.id
        db.session.commit()
        flash("Team updated.", "success")
        return redirect(url_for("chairman.team_detail", team_id=team.id))

    return render_template(
        "chairman/team_form.html", leagues=all_leagues, form=team.__dict__,
        mode="edit", team=team,
    )


@chairman_bp.route("/teams/<int:team_id>/delete", methods=["POST"])
@chairman_required
def delete_team(team_id):
    team = Team.query.get_or_404(team_id)
    if team.players:
        flash(
            "This team still has players registered. "
            "Transfer or remove those players before deleting the team.",
            "error",
        )
        return redirect(url_for("chairman.team_detail", team_id=team.id))
    if team.coaches:
        flash(
            "This team still has a coach assigned. "
            "Reassign the coach before deleting the team.",
            "error",
        )
        return redirect(url_for("chairman.team_detail", team_id=team.id))
    db.session.delete(team)
    db.session.commit()
    flash("Team deleted.", "success")
    return redirect(url_for("chairman.teams"))


# ---------------------------------------------------------------------
# System controls
# ---------------------------------------------------------------------
@chairman_bp.route("/system-controls", methods=["GET", "POST"])
@chairman_required
def system_controls():
    settings = SystemSetting.get_current()

    if request.method == "POST":
        settings.player_update_open = request.form.get("player_update_open") == "on"
        settings.transfer_open = request.form.get("transfer_open") == "on"
        db.session.commit()
        flash("System controls updated.", "success")
        return redirect(url_for("chairman.system_controls"))

    return render_template("chairman/system_controls.html", settings=settings)
