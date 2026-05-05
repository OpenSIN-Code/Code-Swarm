"""Code-Swarm: Plan/Act/Verify modes (stolen from Cline).

Three core modes with approval gates before every side-effect action.
"""

from enum import Enum


class AgentMode(Enum):
    PLAN = "plan"
    ACT = "act"
    VERIFY = "verify"
    YOLO = "yolo"


class ApprovalGate:
    """Approval required before every side-effect action."""

    def __init__(self, mode: AgentMode = AgentMode.ACT):
        self.mode = mode

    def check(self, action: str, risk: str = "low") -> bool:
        if self.mode == AgentMode.YOLO:
            return True
        if self.mode == AgentMode.PLAN:
            return False
        if risk == "high" and self.mode != AgentMode.YOLO:
            return False
        return True


class PlanActVerify:
    """Three-stage execution pipeline."""

    def __init__(self):
        self.mode = AgentMode.PLAN
        self.plan: list[dict] = []
        self.results: list[dict] = []
        self.gate = ApprovalGate()

    def plan_stage(self, task: str, llm_callable) -> list[dict]:
        self.plan = llm_callable(
            f"Create step-by-step plan for: {task}. "
            "Return as JSON array of {step, action, expected}"
        )
        self.mode = AgentMode.ACT
        return self.plan

    def act_stage(self, step: dict, executor_callable) -> dict:
        if not self.gate.check(
            step.get("action", ""),
            step.get("risk", "low")
        ):
            return {"status": "blocked", "reason": "Gate rejected"}
        result = executor_callable(step["action"])
        self.results.append(result)
        return result

    def verify_stage(self, expected: str, actual: str) -> bool:
        self.mode = AgentMode.PLAN
        passed = expected.lower() in actual.lower()
        return passed

    def run_pipeline(self, task: str, llm_callable, executor_callable) -> list[dict]:
        steps = self.plan_stage(task, llm_callable)
        for step in steps:
            result = self.act_stage(step, executor_callable)
            if result.get("status") == "blocked":
                break
            if not self.verify_stage(step.get("expected", ""), str(result)):
                step["retry"] = True
        self.mode = AgentMode.VERIFY
        return self.results
