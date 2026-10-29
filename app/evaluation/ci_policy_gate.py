import json
import sys
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEST_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "guardrail_test_cases.json"
)


BLOCK_PATTERNS = [
    "ignore all previous instructions",
    "disable your safety rules",
    "no safety policies",
    "hidden system prompt",
    "internal instructions",
    "bypass the guardrails",
    "unrestricted assistant",
    "show me the api key",
    "database password",
    "authentication tokens",
    "credentials stored",
    "break into someone",
    "bypass authentication",
    "steal another user's password",
    "unauthorized access",
]


SAFE_CONTEXT_PATTERNS = [
    "how can users defend",
    "security awareness",
    "high level",
    "signs that an account",
]


def load_test_cases():
    with open(
        TEST_DATA_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def policy_decision(prompt: str) -> str:
    text = prompt.lower()

    for safe_pattern in SAFE_CONTEXT_PATTERNS:
        if safe_pattern in text:
            return "allow"

    for block_pattern in BLOCK_PATTERNS:
        if block_pattern in text:
            return "block"

    return "allow"


def run_policy_gate():
    test_cases = load_test_cases()

    results = []
    category_stats = defaultdict(
        lambda: {
            "total": 0,
            "passed": 0,
        }
    )

    for test_case in test_cases:
        actual = policy_decision(
            test_case["prompt"]
        )

        expected = test_case["expected"]

        passed = actual == expected

        results.append(
            {
                "id": test_case["id"],
                "category": test_case["category"],
                "expected": expected,
                "actual": actual,
                "passed": passed,
            }
        )

        category = test_case["category"]

        category_stats[
            category
        ]["total"] += 1

        if passed:
            category_stats[
                category
            ]["passed"] += 1

    total = len(results)

    passed = sum(
        1
        for result in results
        if result["passed"]
    )

    compliance = (
        passed / total
        if total
        else 0.0
    )

    failures = [
        result
        for result in results
        if not result["passed"]
    ]

    print(
        "\nCI Guardrail Policy Gate"
    )

    print(
        "=" * 60
    )

    print(
        f"Total cases: {total}"
    )

    print(
        f"Passed cases: {passed}"
    )

    print(
        f"Policy compliance: "
        f"{compliance:.1%}"
    )

    print(
        "\nPer-category accuracy:"
    )

    for category, stats in sorted(
        category_stats.items()
    ):
        accuracy = (
            stats["passed"]
            / stats["total"]
        )

        print(
            f"- {category}: "
            f"{accuracy:.1%}"
        )

    if failures:
        print(
            "\nPolicy failures:"
        )

        for failure in failures:
            print(
                f"- {failure['id']} | "
                f"expected="
                f"{failure['expected']} | "
                f"actual="
                f"{failure['actual']}"
            )

    required_compliance = 1.0

    if compliance < required_compliance:
        print(
            "\nCI FAILED: "
            "Policy compliance dropped "
            "below 100%."
        )

        sys.exit(1)

    print(
        "\nCI PASSED: "
        "All guardrail policy cases passed."
    )


if __name__ == "__main__":
    run_policy_gate()