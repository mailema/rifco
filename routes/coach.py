import os
import uuid

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    current_app, abort,
)
from flask_login import current_user

from extensions import db
from models import Player, Team, SystemSetting
from constants import PLAYER_POSITIONS
from routes.decorators import coach_required

coach_bp = Blueprint("coach", __name__, url_prefix="/coach")


def _allowed_image(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def _save_player_picture(file_storage):
    """Save an uploaded picture with a random, collision-proof name
    and return the path to store on the Player record. Returns None
    if no file was provided."""
    if not file_storage or not file_storage.filename:
        return None
    if not _allowed_image(file_storage.filename):
        raise ValueError("Only PNG, JPG, JPEG or WEBP images are allowed.")

    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, safe_name))
    return f"uploads/players/{safe_name}"


def _get_coach_team():
    """The coach's team is always derived from the authenticated
    Member record - never trusted from client input."""
    return current_user.team


@coach_bp.route("/")
@coach_required
def dashboard():
    team = _get_coach_team()
    settings = SystemSetting.get_current()
    if team is None:
        return render_template("coach/dashboard.html", team=None, players=[], settings=settings)
    players = Player.query.filter_by(team_id=team.id).order_by(Player.name).all()
    return render_template(
        "coach/dashboard.html", team=team, players=players, settings=settings,
    )


@coach_bp.route("/players")
@coach_required
def players():
    team = _get_coach_team()
    if team is None:
        flash("You are not currently assigned to a team. Contact the Chairman.", "warning")
        return redirect(url_for("coach.dashboard"))

    q = (request.args.get("q") or "").strip()
    query = Player.query.filter_by(team_id=team.id)
    if q:
        query = query.filter(
            db.or_(Player.name.ilike(f"%{q}%"), Player.player_id.ilike(f"%{q}%"))
        )
    all_players = query.order_by(Player.name).all()
    return render_template("coach/players.html", players=all_players, team=team, q=q)


@coach_bp.route("/players/register", methods=["GET", "POST"])
@coach_required
def register_player():
    team = _get_coach_team()
    if team is None:
        flash("You are not currently assigned to a team. Contact the Chairman.", "warning")
        return redirect(url_for("coach.dashboard"))

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        position = (request.form.get("position") or "").strip()
        player_id = (request.form.get("player_id") or "").strip()
        phone = (request.form.get("phone") or "").strip()

        errors = []
        if not name:
            errors.append("Player name is required.")
        if position not in PLAYER_POSITIONS:
            errors.append("A valid position must be selected.")
        if not player_id:
            errors.append("Player ID is required.")
        elif Player.query.filter_by(player_id=player_id).first():
            errors.append("This Player ID is already registered (Player IDs are unique across RIFCO).")
        if not phone:
            errors.append("Phone is required.")

        picture_path = None
        picture_file = request.files.get("picture")
        if picture_file and picture_file.filename:
            try:
                picture_path = _save_player_picture(picture_file)
            except ValueError as exc:
                errors.append(str(exc))

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "coach/player_form.html", positions=PLAYER_POSITIONS,
                form=request.form, mode="create", team=team,
            )

        player = Player(
            name=name, position=position, player_id=player_id, phone=phone,
            team_id=team.id, picture=picture_path,
        )
        db.session.add(player)
        db.session.commit()
        flash(f"{name} registered to {team.team_name}.", "success")
        return redirect(url_for("coach.players"))

    return render_template(
        "coach/player_form.html", positions=PLAYER_POSITIONS, form={}, mode="create",
        team=team,
    )


@coach_bp.route("/players/<int:player_id>")
@coach_required
def player_detail(player_id):
    team = _get_coach_team()
    player = Player.query.get_or_404(player_id)
    if team is None or player.team_id != team.id:
        # A coach may never view another team's player via a guessed ID.
        abort(403)
    settings = SystemSetting.get_current()
    return render_template("coach/player_detail.html", player=player, settings=settings)


@coach_bp.route("/players/<int:player_id>/edit", methods=["GET", "POST"])
@coach_required
def update_player(player_id):
    team = _get_coach_team()
    player = Player.query.get_or_404(player_id)

    if team is None or player.team_id != team.id:
        abort(403)

    settings = SystemSetting.get_current()
    if not settings.player_update_open:
        flash("Player updates are currently closed by the Chairman.", "warning")
        return redirect(url_for("coach.player_detail", player_id=player.id))

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        position = (request.form.get("position") or "").strip()
        phone = (request.form.get("phone") or "").strip()

        errors = []
        if not name:
            errors.append("Player name is required.")
        if position not in PLAYER_POSITIONS:
            errors.append("A valid position must be selected.")
        if not phone:
            errors.append("Phone is required.")

        picture_file = request.files.get("picture")
        new_picture_path = player.picture
        if picture_file and picture_file.filename:
            try:
                new_picture_path = _save_player_picture(picture_file)
            except ValueError as exc:
                errors.append(str(exc))

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "coach/player_form.html", positions=PLAYER_POSITIONS,
                form=request.form, mode="edit", player=player, team=team,
            )

        player.name = name
        player.position = position
        player.phone = phone
        player.picture = new_picture_path
        db.session.commit()
        flash("Player updated.", "success")
        return redirect(url_for("coach.player_detail", player_id=player.id))

    return render_template(
        "coach/player_form.html", positions=PLAYER_POSITIONS, form=player.__dict__,
        mode="edit", player=player, team=team,
    )


@coach_bp.route("/players/<int:player_id>/delete", methods=["POST"])
@coach_required
def delete_player(player_id):
    team = _get_coach_team()
    player = Player.query.get_or_404(player_id)
    if team is None or player.team_id != team.id:
        abort(403)
    db.session.delete(player)
    db.session.commit()
    flash("Player removed from roster.", "success")
    return redirect(url_for("coach.players"))
