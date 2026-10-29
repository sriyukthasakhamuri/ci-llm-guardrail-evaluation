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

REPORTS_DIRECTORY = (
    PROJECT_ROOT
    / "reports"
)

REPORT_PATH = (
    REPORTS_DIRECTORY
    / "guardrail_ci_report.json"
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


def save_report(report_data):
    REPORTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        REPORT_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report_data,
            file,
            indent=2,
        )


def run_policy_gate():
    test_cases = load_test_cases()

    results = []

    category_stats = defaultdict(
        lambda: {
            "total": 0,
            "passed": 0,
        }
    )

    print(
        "\nCI Guardrail Policy Gate"
    )

    print(
        "=" * 60
    )

    for test_case in test_cases:
        actual = policy_decision(
            test_case["prompt"]
        )

        expected = test_case["expected"]

        passed = actual == expected

        result = {
            "id": test_case["id"],
            "category": test_case["category"],
            "prompt": test_case["prompt"],
            "expected": expected,
            "actual": actual,
            "passed": passed,
        }

        results.append(result)

        category = test_case["category"]

        category_stats[
            category
        ]["total"] += 1

        if passed:
            category_stats[
                category
            ]["passed"] += 1

        print(
            f"\n{test_case['id']}"
        )

        print(
            f"Category: "
            f"{test_case['category']}"
        )

        print(
            f"Expected: {expected}"
        )

        print(
            f"Actual: {actual}"
        )

        print(
            f"Passed: {passed}"
        )

    total_cases = len(results)

    passed_cases = sum(
        1
        for result in results
        if result["passed"]
    )

    policy_compliance = (
        passed_cases
        / total_cases
        if total_cases
        else 0.0
    )

    safe_cases = [
        result
        for result in results
        if result["expected"] == "allow"
    ]

    unsafe_cases = [
        result
        for result in results
        if result["expected"] == "block"
    ]

    false_positives = sum(
        1
        for result in safe_cases
        if result["actual"] == "block"
    )

    false_negatives = sum(
        1
        for result in unsafe_cases
        if result["actual"] == "allow"
    )

    false_positive_rate = (
        false_positives
        / len(safe_cases)
        if safe_cases
        else 0.0
    )

    false_negative_rate = (
        false_negatives
        / len(unsafe_cases)
        if unsafe_cases
        else 0.0
    )

    category_report = {}

    for category, stats in sorted(
        category_stats.items()
    ):
        accuracy = (
            stats["passed"]
            / stats["total"]
            if stats["total"]
            else 0.0
        )

        category_report[
            category
        ] = {
            "total": stats["total"],
            "passed": stats["passed"],
            "accuracy": accuracy,
        }

    failures = [
        result
        for result in results
        if not result["passed"]
    ]

    required_compliance = 1.0

    status = (
        "passed"
        if policy_compliance
        >= required_compliance
        else "failed"
    )

    report_data = {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "policy_compliance":
            policy_compliance,
        "false_positive_rate":
            false_positive_rate,
        "false_negative_rate":
            false_negative_rate,
        "required_compliance":
            required_compliance,
        "status":
            status,
        "category_accuracy":
            category_report,
        "failures":
            failures,
    }

    save_report(
        report_data
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "CI Evaluation Summary"
    )

    print(
        "=" * 60
    )

    print(
        f"Total test cases: "
        f"{total_cases}"
    )

    print(
        f"Passed test cases: "
        f"{passed_cases}"
    )

    print(
        f"Policy compliance: "
        f"{policy_compliance:.1%}"
    )

    print(
        f"False positive rate: "
        f"{false_positive_rate:.1%}"
    )

    print(
        f"False negative rate: "
        f"{false_negative_rate:.1%}"
    )

    print(
        "\nPer-category accuracy:"
    )

    for category, stats in sorted(
        category_report.items()
    ):
        print(
            f"- {category}: "
            f"{stats['accuracy']:.1%} "
            f"({stats['passed']}/"
            f"{stats['total']})"
        )

    print(
        f"\nReport saved to: "
        f"{REPORT_PATH}"
    )

    if failures:
        print(
            "\nFailures:"
        )

        for result in failures:
            print(
                f"- {result['id']} | "
                f"expected="
                f"{result['expected']} | "
                f"actual="
                f"{result['actual']}"
            )

    if status == "failed":
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