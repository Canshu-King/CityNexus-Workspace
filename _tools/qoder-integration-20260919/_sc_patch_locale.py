"""Add the unresolved-cursor copy to both locale dictionaries."""

import io

PATH = "frontend/src/i18n/LocaleContext.tsx"
text = io.open(PATH, encoding="utf-8", newline="").read()

en_old = '  "live.awaitingPlan": "Awaiting plan",'
en_new = "\n".join(
    [
        '  "live.awaitingPlan": "Awaiting plan",',
        "  // A cursor that names an activity the active plan does not contain is a",
        '  // different fact from "no plan yet"; the UI must not claim the latter.',
        '  "live.unresolvedStep": "Execution position unresolved",',
        '  "live.unresolvedStepHint": "The saved position points at a step this plan no longer contains, so no current or next step can be shown honestly.",',
    ]
)
assert text.count(en_old) == 1, "en anchor not unique"
text = text.replace(en_old, en_new, 1)

zh_old = '  "live.awaitingPlan": "等待方案",'
zh_new = "\n".join(
    [
        '  "live.awaitingPlan": "等待方案",',
        '  "live.unresolvedStep": "执行位置无法确认",',
        '  "live.unresolvedStepHint": "已保存的位置指向当前方案中不再存在的步骤，无法如实显示当前或下一步。",',
    ]
)
assert text.count(zh_old) == 1, "zh anchor not unique"
text = text.replace(zh_old, zh_new, 1)

io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("locale keys added")
