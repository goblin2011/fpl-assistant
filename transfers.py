"""Budget-constrained transfer suggestions.

Builds three tiers — best single transfer, best 2-transfer combo, best
3-transfer combo — each respecting the manager's actual bank balance rather
than an arbitrary price step-up. Capped at 3 transfers deliberately: beyond
that the combinatorics stop being "one quick decision" and the free-transfer
cost (-4 pts per transfer past the first) usually isn't worth it anyway.
"""
from itertools import combinations
from typing import Optional

from model import PlayerScore

# How many of the manager's weakest players to consider replacing at all.
# Kept small since it's also the pool the 2- and 3-transfer combos search
# over (choose(8, 3) = 56 combinations, trivial to check exhaustively).
CANDIDATE_POOL_SIZE = 8
MIN_SCORE_GAIN = 5.0


def _best_replacement(owned: dict, all_scores: dict, owned_ids: set) -> Optional[PlayerScore]:
    pool = [
        p for p in all_scores.values()
        if p.position == owned["position"]
        and p.id not in owned_ids
        and p.score > owned["score"] + MIN_SCORE_GAIN
    ]
    if not pool:
        return None
    return max(pool, key=lambda p: p.score)


def _swap_summary(owned: dict, replacement: PlayerScore) -> dict:
    return {
        "out": {"name": owned["name"], "score": owned["score"], "price": owned["price"]},
        "in": {"name": replacement.name, "score": replacement.score, "price": replacement.price},
        "net_cost": round(replacement.price - owned["price"], 1),
        "score_gain": round(replacement.score - owned["score"], 1),
    }


def build_transfer_plan(my_players: list[dict], all_scores: dict, bank: float) -> dict:
    owned_ids = {p["id"] for p in my_players}
    weakest = sorted(my_players, key=lambda p: p["score"])[:CANDIDATE_POOL_SIZE]

    candidates = []
    used_incoming_ids: set = set()
    for owned in weakest:
        replacement = _best_replacement(owned, all_scores, owned_ids | used_incoming_ids)
        if replacement:
            used_incoming_ids.add(replacement.id)
            candidates.append(_swap_summary(owned, replacement))

    def affordable_combos(size: int):
        for combo in combinations(candidates, size):
            total_cost = round(sum(c["net_cost"] for c in combo), 1)
            if total_cost <= bank:
                yield combo, total_cost

    def best_combo(size: int):
        best, best_cost, best_gain = None, None, -1.0
        for combo, cost in affordable_combos(size):
            gain = sum(c["score_gain"] for c in combo)
            if gain > best_gain:
                best, best_cost, best_gain = combo, cost, gain
        if best is None:
            return None
        return {
            "transfers": list(best),
            "total_cost": best_cost,
            "total_score_gain": round(best_gain, 1),
        }

    return {
        "bank": bank,
        "best_single_transfer": best_combo(1),
        "best_two_transfers": best_combo(2) if len(candidates) >= 2 else None,
        "best_three_transfers": best_combo(3) if len(candidates) >= 3 else None,
    }
