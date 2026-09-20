"""
Centralized authorization decorators.

Every protected route enforces its permission on the SERVER SIDE.
Hiding a nav link is never treated as security - a signed-in user
who manually visits or POSTs to a restricted URL must still be
blocked here.
"""

from functools import wraps

from flask import abort
from flask_login import current_user, login_required  # re-exported for routes

from constants import CHAIRMAN_RANK, COACH_RANK, TRANSFER_COMMITTEE_RANK

__all__ = ["login_required", "chairman_required", "coach_required", "transfer_required"]


def chairman_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rank != CHAIRMAN_RANK:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def coach_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rank != COACH_RANK:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def transfer_required(view):
    """
    Authorization for the Transfer Portal.

    Only the "Transfer Committee" rank may use this portal - not the
    Chairman, not a Coach, not any other rank. Each rank is confined
    to its own portal (Chairman -> Chairman Portal, Coach -> Coach
    Portal, Transfer Committee -> Transfer Portal), so this check is
    deliberately an exact rank match rather than "Chairman or
    Transfer Committee" - the Chairman does not get an automatic
    back door into this portal.
    """

    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rank != TRANSFER_COMMITTEE_RANK:
            abort(403)
        return view(*args, **kwargs)

    return wrapped
