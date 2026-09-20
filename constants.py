"""
Centralized, controlled value lists used across the application.
Keeping these in one place means the database layer, forms, and
templates never disagree about what a valid rank or position is.
"""

# Organizational ranks. "Coach" is the only rank that can be linked
# to a team roster. "Transfer Committee" is the only rank authorized
# to use the Transfer Portal (see routes/decorators.py).
MEMBER_RANKS = [
    "Chairman",
    "Vice Chairman",
    "Secretary",
    "Assistant Secretary",
    "Treasurer",
    "Financial Secretary",
    "Organization Secretary 1",
    "Organization Secretary 2",
    "Welfare",
    "Auditor",
    "Legal Advisor",
    "P.R.O 1",
    "P.R.O 2",
    "P.R.O 3",
    "Coach",
    "Transfer Committee",
]

CHAIRMAN_RANK = "Chairman"
COACH_RANK = "Coach"
TRANSFER_COMMITTEE_RANK = "Transfer Committee"

# Football playing positions. Kept broad for now; can be extended to
# more specific positions (Centre Back, Left Winger, Striker, etc.)
# without any structural change.
PLAYER_POSITIONS = [
    "Goalkeeper",
    "Defender",
    "Midfielder",
    "Forward",
]

