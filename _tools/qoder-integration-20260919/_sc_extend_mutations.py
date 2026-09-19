"""Extend the mutation set with the resolver's own branches.

The C4 fail-closed branch inside the acceptance endpoint turned out to be
unreachable through HTTP (the feasibility gate intercepts first), so it survives
as defence in depth.  The counting it depends on lives in
`app/replanning/commitment_remap.py`, and that is what these mutations attack.
"""

import io

PATH = "_sc_mutation_check.py"
text = io.open(PATH, encoding="utf-8", newline="").read()

old_tail = '''    (
        "F: an unresolvable C4 is skipped instead of failing closed",
        "app/main.py",
        """            if protected:""",
        """            if False:""",
    ),
]'''
new_tail = '''    (
        "F: an unresolvable C4 is skipped instead of failing closed",
        "app/main.py",
        """            if protected:""",
        """            if False:""",
    ),
    (
        "F1: the resolver picks the first of many instead of AMBIGUOUS",
        "app/replanning/commitment_remap.py",
        """    if len(matches) > 1:
        raise RemapConflict(
            f"{subject} remap is AMBIGUOUS on the active Journey plan "
            f"({len(matches)} candidates carry the same identity)",
            matched=len(matches),
        )""",
        """    if len(matches) > 1:
        return matches[0]""",
    ),
    (
        "F2: the resolver returns nothing instead of failing on zero matches",
        "app/replanning/commitment_remap.py",
        """    raise RemapConflict(
        f"{subject} cannot be attached to the active Journey plan",
        matched=0,
    )""",
        """    return None  # SABOTAGE""",
    ),
    (
        "F3: identity falls back to suffix similarity",
        "app/replanning/commitment_remap.py",
        """        if identity.strong & candidate_strong:""",
        """        if identity.strong & candidate_strong or any(
            candidate.endswith(term) for candidate in candidate_strong | candidate_generic
            for term in identity.strong | identity.generic if term
        ):""",
    ),
    (
        "F4: the scheduled instant is not part of the anchor",
        "app/replanning/commitment_remap.py",
        """        if not _same_instant(identity.scheduled_at, moment):
            continue""",
        """        if False:
            continue""",
    ),
]'''
assert old_tail in text
text = text.replace(old_tail, new_tail, 1)
io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("mutation set extended")
