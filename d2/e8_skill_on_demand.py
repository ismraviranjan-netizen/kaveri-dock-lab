# E8 · Skills: the label on every call, the manual on demand  (objective 2.5)
#
#   A Skill is a folder with a SKILL.md. Its short description (the label) rides on every call; the body (the
#   manual) is loaded only when the model decides it applies. The Skill is uploaded ONCE to your workspace,
#   then referenced by id. Compare the daily token bill of "SOP pack in every prompt" with "label always,
#   manual on demand".
#
#   Live only for the upload: Skills live in your Anthropic workspace, and the message that uses one needs the
#   code execution tool and its beta flag. On battery the stand-in returns a canned answer.
#
# Run on battery:  DRY_RUN=1 python e8_skill_on_demand.py    Run live:  python e8_skill_on_demand.py

from common import make_client, create_message, text_of, served_by, MODEL, DRY_RUN

NAME = "customs-triage"
SKILL_MD = """---
name: customs-triage
description: Triages customs holds on Kaveri shipments under SOP 214 -
  e-way bill re-filing, document checks and release steps. Use when a
  dispatcher asks about a customs hold, an e-way bill mismatch or a
  held consignment.
---
# Customs triage (SOP 214)
1. Check whether the e-way bill was filed today.
   If not, re-file it (SOP 214 s4).
2. Check that the invoice and the HSN code match the bill of entry.
3. If both are clean, ask customs for the release time and tell
   the customer.
"""

# Kaveri's numbers, in tokens: the SOP pack, a Skill's label, a Skill's body; calls a day, times the Skill opens
PACK, META, BODY = 8000, 95, 3800
CALLS, LOADS = 5600, 616


if __name__ == "__main__":
    print("# E8 · skill on demand · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL))

    # STEP 1. Upload once. Later runs find it by name in the workspace.
    client = make_client()
    skill = next((s for s in client.skills.list(source="custom") if s.display_name == NAME), None)
    if skill is None:
        skill = client.skills.create(display_name=NAME, files=[(NAME + "/SKILL.md", SKILL_MD.encode(), "text/markdown")])
        print("  uploaded skill " + NAME)
    print("  skill id " + str(skill.id) + " | name " + str(len(NAME)) + " chars (max 64)")

    # STEP 2. One call that may open the manual. Up to 20 Skills per request.
    reply = create_message(betas=["code-execution-2025-08-25"],
                           model=MODEL, max_tokens=4096, output_config={"effort": "low"},
                           container={"skills": [{"type": "custom", "skill_id": skill.id, "version": "latest"}]},
                           tools=[{"type": "code_execution_20260521", "name": "code_execution"}],
                           messages=[{"role": "user", "content": "KF-2481 is on customs hold. What first?"}])
    print()
    print("=== the answer ===")
    print("  " + text_of(reply))
    u = reply.usage
    print("  paid: " + format(u.input_tokens, ",") + " in, " + format(u.output_tokens, ",") + " out | " + str(reply.stop_reason) + served_by(reply))

    # STEP 3. The arithmetic of the two bills. No model call.
    print()
    print("=== two bills a day, Kaveri's numbers ===")
    print("  SOP pack in every prompt : " + format(PACK * CALLS / 1e6, ".1f") + "M tokens a day")
    print("  as a Skill               : " + str(META) + " x " + format(CALLS, ",") + " + " + format(BODY, ",") + " x " + str(LOADS)
          + " = " + format((META * CALLS + BODY * LOADS) / 1e6, ".2f") + "M tokens a day")
