"""Greedy squad optimizer.

Builds a valid 15-man FPL squad (2 GKP / 5 DEF / 5 MID / 3 FWD, budget cap,
max 3 players per real-life team) that maximizes total model score.

Uses a greedy/value-based heuristic rather than a full ILP solver: simple,
fast, no extra dependencies, and close enough to optimal for a v1 — good
enough to be genuinely useful, not claiming to be provably optimal.
"""
from .model import PlayerScore

SQUAD_SHAPE = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
MAX_PER_TEAM = 3
BUDGET = 100.0


def build_squad(players: list[PlayerScore], budget: float = BUDGET) -> dict:
    by_position: dict[str, list[PlayerScore]] = {pos: [] for pos in SQUAD_SHAPE}
    for p in players:
        by_position.setdefault(p.position, []).append(p)
    for pos in by_position:
        by_position[pos].sort(key=lambda p: p.score, reverse=True)

    # Cheapest available price per position, used to size the budget reserve
    # kept aside for slots not yet filled (a flat estimate under-reserves for
    # pricier positions like FWD/GKP and can strand the last slot unfilled).
    min_price_by_pos = {
        pos: min((p.price for p in cands), default=4.0)
        for pos, cands in by_position.items()
    }

    squad: list[PlayerScore] = []
    team_counts: dict[str, int] = {}
    remaining_budget = budget

    # Fill scarcer/cheaper positions (GKP, DEF) before MID/FWD stars eat the
    # budget, then greedily fill each slot with the best-scoring affordable
    # player that respects the 3-per-team cap.
    fill_order = ["GKP", "DEF", "FWD", "MID"]
    slots = [(pos, i) for pos in fill_order for i in range(SQUAD_SHAPE[pos])]

    def reserve_for_remaining(current_pos: str) -> float:
        remaining_counts = dict(SQUAD_SHAPE)
        remaining_counts[current_pos] -= 1
        filled_so_far = {pos: 0 for pos in SQUAD_SHAPE}
        for p in squad:
            filled_so_far[p.position] = filled_so_far.get(p.position, 0) + 1
        reserve = 0.0
        for pos, total in SQUAD_SHAPE.items():
            still_needed = total - filled_so_far.get(pos, 0)
            if pos == current_pos:
                still_needed -= 1
            reserve += max(still_needed, 0) * min_price_by_pos.get(pos, 4.0)
        return reserve

    for pos, _ in slots:
        candidates = by_position.get(pos, [])
        picked = None
        reserve = reserve_for_remaining(pos)
        for cand in candidates:
            if cand in squad:
                continue
            if team_counts.get(cand.team, 0) >= MAX_PER_TEAM:
                continue
            if cand.price > remaining_budget - reserve:
                continue
            picked = cand
            break
        if picked is None:
            # Relax to cheapest eligible player at this position that still
            # leaves enough for whatever remains after this pick.
            for cand in sorted(candidates, key=lambda p: p.price):
                if cand in squad:
                    continue
                if team_counts.get(cand.team, 0) >= MAX_PER_TEAM:
                    continue
                if cand.price <= remaining_budget:
                    picked = cand
                    break
        if picked:
            squad.append(picked)
            team_counts[picked.team] = team_counts.get(picked.team, 0) + 1
            remaining_budget -= picked.price

    starting_xi, bench = pick_starting_xi(squad)

    return {
        "squad": squad,
        "starting_xi": starting_xi,
        "bench": bench,
        "total_cost": round(budget - remaining_budget, 1),
        "budget_remaining": round(remaining_budget, 1),
        "captain": starting_xi[0] if starting_xi else None,
        "vice_captain": starting_xi[1] if len(starting_xi) > 1 else None,
    }


def pick_starting_xi(squad: list[PlayerScore]) -> tuple[list[PlayerScore], list[PlayerScore]]:
    """Pick best valid formation (1 GKP, 3-5 DEF, 2-5 MID, 1-3 FWD, 11 total)."""
    by_pos: dict[str, list[PlayerScore]] = {"GKP": [], "DEF": [], "MID": [], "FWD": []}
    for p in squad:
        by_pos[p.position].append(p)
    for pos in by_pos:
        by_pos[pos].sort(key=lambda p: p.score, reverse=True)

    starting = [by_pos["GKP"][0]] if by_pos["GKP"] else []
    mins = {"DEF": 3, "MID": 2, "FWD": 1}
    for pos, n in mins.items():
        starting.extend(by_pos[pos][:n])

    remaining_pool = []
    for pos in ("DEF", "MID", "FWD"):
        remaining_pool.extend(by_pos[pos][mins[pos]:])
    remaining_pool.sort(key=lambda p: p.score, reverse=True)

    max_def, max_mid, max_fwd = 5, 5, 3
    counts = {"DEF": mins["DEF"], "MID": mins["MID"], "FWD": mins["FWD"]}
    while len(starting) < 11 and remaining_pool:
        for i, cand in enumerate(remaining_pool):
            limit = {"DEF": max_def, "MID": max_mid, "FWD": max_fwd}[cand.position]
            if counts[cand.position] < limit:
                starting.append(cand)
                counts[cand.position] += 1
                remaining_pool.pop(i)
                break
        else:
            break

    starting.sort(key=lambda p: p.score, reverse=True)
    bench = [p for p in squad if p not in starting]
    bench.sort(key=lambda p: p.score, reverse=True)
    return starting, bench
