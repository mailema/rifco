from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user

from extensions import db
from models import Player, Team, Transfer, SystemSetting
from routes.decorators import transfer_required

transfer_bp = Blueprint("transfer", __name__, url_prefix="/transfer")


@transfer_bp.route("/")
@transfer_required
def portal():
    settings = SystemSetting.get_current()
    teams = Team.query.order_by(Team.team_name).all()
    return render_template("transfer/portal.html", settings=settings, teams=teams)


@transfer_bp.route("/search", methods=["POST"])
@transfer_required
def search_player():
    settings = SystemSetting.get_current()
    teams = Team.query.order_by(Team.team_name).all()

    player_id = (request.form.get("player_id") or "").strip()
    from_team_id = request.form.get("from_team_id")

    if not player_id or not from_team_id:
        flash("Player ID and the current team are both required to search.", "error")
        return redirect(url_for("transfer.portal"))

    from_team = Team.query.get(from_team_id)
    if from_team is None:
        flash("Selected team does not exist.", "error")
        return redirect(url_for("transfer.portal"))

    player = Player.query.filter_by(player_id=player_id).first()
    if player is None:
        flash(f"No player found with Player ID '{player_id}'.", "error")
        return render_template(
            "transfer/portal.html", settings=settings, teams=teams,
        )

    if player.team_id != from_team.id:
        flash(
            "This Player ID does not belong to the selected team. "
            "Transfers can only be initiated from the player's actual current team.",
            "error",
        )
        return render_template(
            "transfer/portal.html", settings=settings, teams=teams,
        )

    return render_template(
        "transfer/portal.html", settings=settings, teams=teams,
        found_player=player, from_team=from_team,
    )


@transfer_bp.route("/execute", methods=["POST"])
@transfer_required
def execute_transfer():
    settings = SystemSetting.get_current()
    if not settings.transfer_open:
        flash("Transfers are currently closed by the Chairman.", "error")
        return redirect(url_for("transfer.portal"))

    player_id = (request.form.get("player_id") or "").strip()
    from_team_id = request.form.get("from_team_id")
    to_team_id = request.form.get("to_team_id")

    if not player_id or not from_team_id or not to_team_id:
        flash("Player, current team, and destination team are all required.", "error")
        return redirect(url_for("transfer.portal"))

    player = Player.query.filter_by(player_id=player_id).first()
    from_team = Team.query.get(from_team_id)
    to_team = Team.query.get(to_team_id)

    if player is None:
        flash("Player not found.", "error")
        return redirect(url_for("transfer.portal"))
    if from_team is None or to_team is None:
        flash("One of the selected teams does not exist.", "error")
        return redirect(url_for("transfer.portal"))
    if player.team_id != from_team.id:
        flash("Player does not currently belong to the selected FROM team.", "error")
        return redirect(url_for("transfer.portal"))
    if from_team.id == to_team.id:
        flash("A player cannot be transferred to the team they already belong to.", "error")
        return redirect(url_for("transfer.portal"))

    # All checks passed - perform the transfer as a single transaction:
    # move the player, then record the history. Either both succeed or
    # neither does.
    try:
        transfer_record = Transfer(
            player_id=player.id,
            from_team_id=from_team.id,
            to_team_id=to_team.id,
            transferred_by=current_user.id,
        )
        player.team_id = to_team.id
        db.session.add(transfer_record)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("The transfer could not be completed due to a system error. Nothing was changed.", "error")
        return redirect(url_for("transfer.portal"))

    flash(
        f"{player.name} transferred from {from_team.team_name} to {to_team.team_name}.",
        "success",
    )
    return redirect(url_for("transfer.history"))


@transfer_bp.route("/history")
@transfer_required
def history():
    q = (request.args.get("q") or "").strip()
    query = Transfer.query
    if q:
        query = query.join(Player).filter(
            db.or_(Player.name.ilike(f"%{q}%"), Player.player_id.ilike(f"%{q}%"))
        )
    transfers = query.order_by(Transfer.transferred_at.desc()).all()
    return render_template("transfer/history.html", transfers=transfers, q=q)
