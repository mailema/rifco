from flask import Blueprint, render_template

from models import League, Team, Player, Member
from constants import COACH_RANK

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    # Real counts once data exists; the homepage never fabricates
    # numbers, it just shows zero gracefully on a fresh database.
    stats = {
        "leagues": League.query.count(),
        "teams": Team.query.count(),
        "players": Player.query.count(),
        "coaches": Member.query.filter_by(rank=COACH_RANK).count(),
    }
    leagues = League.query.order_by(League.name).limit(3).all()
    return render_template("index.html", stats=stats, leagues=leagues)


@public_bp.route("/about")
def about():
    return render_template("about.html")


@public_bp.route("/leagues")
def leagues():
    all_leagues = League.query.order_by(League.name).all()
    return render_template("leagues_public.html", leagues=all_leagues)


@public_bp.route("/teams")
def teams():
    all_teams = Team.query.order_by(Team.team_name).all()
    return render_template("teams_public.html", teams=all_teams)


@public_bp.route("/players")
def players():
    all_players = Player.query.order_by(Player.name).all()
    return render_template("players_public.html", players=all_players)


@public_bp.route("/contact")
def contact():
    return render_template("contact.html")
