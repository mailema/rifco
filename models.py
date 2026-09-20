"""
RIFCO database models.

Kept as a single models.py rather than a models/ package: at this
project's current size a handful of related classes are easier to
scan and cross-reference in one file. If the schema grows
significantly, splitting into models/member.py, models/team.py, etc.
is a safe, mechanical refactor - nothing here depends on the file
layout.

Relationships:

    League 1---* Team
    Team   1---* Player
    Team   1---* Member   (coaches only; non-coaches have team_id = None)
    Player *---1 Team
    Transfer *---1 Player
    Transfer *---1 Team (from_team)
    Transfer *---1 Team (to_team)
"""

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from constants import COACH_RANK, TRANSFER_COMMITTEE_RANK


def utcnow():
    return datetime.now(timezone.utc)


class League(db.Model):
    __tablename__ = "leagues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    teams = db.relationship(
        "Team", back_populates="league", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<League id={self.id} name={self.name!r}>"


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(120), unique=True, nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey("leagues.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    league = db.relationship("League", back_populates="teams")
    players = db.relationship(
        "Player", back_populates="team", cascade="all, delete-orphan"
    )
    coaches = db.relationship("Member", back_populates="team")

    def __repr__(self):
        return f"<Team id={self.id} name={self.team_name!r}>"


class Member(UserMixin, db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    member_id = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    rank = db.Column(db.String(50), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    team = db.relationship("Team", back_populates="coaches")

    # ---- password helpers -------------------------------------------
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    # ---- role helpers --------------------------------------------
    @property
    def is_chairman(self) -> bool:
        return self.rank == "Chairman"

    @property
    def is_coach(self) -> bool:
        return self.rank == COACH_RANK

    @property
    def is_transfer_committee(self) -> bool:
        return self.rank == TRANSFER_COMMITTEE_RANK

    # Flask-Login uses the primary key as the session identifier.
    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<Member id={self.id} member_id={self.member_id!r} rank={self.rank!r}>"


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    player_id = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    picture = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    team = db.relationship("Team", back_populates="players")

    def __repr__(self):
        return f"<Player id={self.id} player_id={self.player_id!r} team_id={self.team_id}>"


class Transfer(db.Model):
    __tablename__ = "transfers"
    __table_args__ = (
        db.CheckConstraint("from_team_id != to_team_id", name="ck_transfer_teams_differ"),
    )

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    from_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    to_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    # Nullable for now; will reference the Member who performed the
    # transfer once that data is wired up at the route layer.
    transferred_by = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=True)
    transferred_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    player = db.relationship("Player")
    from_team = db.relationship("Team", foreign_keys=[from_team_id])
    to_team = db.relationship("Team", foreign_keys=[to_team_id])
    performed_by = db.relationship("Member", foreign_keys=[transferred_by])

    def __repr__(self):
        return f"<Transfer id={self.id} player_id={self.player_id} {self.from_team_id}->{self.to_team_id}>"


class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)
    player_update_open = db.Column(db.Boolean, default=False, nullable=False)
    transfer_open = db.Column(db.Boolean, default=False, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<SystemSetting player_update_open={self.player_update_open} "
            f"transfer_open={self.transfer_open}>"
        )

    @staticmethod
    def get_current():
        """Return the single settings row, creating it with safe
        defaults if it does not exist yet."""
        setting = SystemSetting.query.first()
        if setting is None:
            setting = SystemSetting(player_update_open=False, transfer_open=False)
            db.session.add(setting)
            db.session.commit()
        return setting
