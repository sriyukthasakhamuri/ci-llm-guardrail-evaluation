import statistics
import time
from pathlib import Path

import requests
from nemoguardrails import LLMRails, RailsConfig


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GUARDRAIL_CONFIG_PATH = (
    PROJECT_ROOT
    / "app"
    / "guardrails"
)

OLLAMA_URL = (
    "http://localhost:11434/v1/chat/completions"
)

MODEL_NAME = "llama3.2:3b"

RUNS = 5

TEST_PROMPT = (
    "Explain CI/CD in one short sentence."
)


config = RailsConfig.from_path(
    str(GUARDRAIL_CONFIG_PATH)
)

rails = LLMRails(config)


def call_ollama_direct(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0,
        },
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    return data["choices"][0]["message"]["content"]


def call_guarded(prompt: str) -> str:
    response = rails.generate(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ]
    )

    return response["content"]


def measure_latency(
    function,
    prompt: str,
) -> float:

    start = time.perf_counter()

    function(prompt)

    end = time.perf_counter()

    return (
        end - start
    ) * 1000


def run_warmup() -> None:
    print(
        "Running warm-up requests..."
    )

    call_ollama_direct(
        TEST_PROMPT
    )

    call_guarded(
        TEST_PROMPT
    )

    print(
        "Warm-up complete.\n"
    )


def run_benchmark() -> None:
    run_warmup()

    baseline_latencies = []
    guarded_latencies = []
    overhead_latencies = []

    print(
        "CI LLM Guardrail Latency Benchmark"
    )

    print(
        "=" * 60
    )

    for run_number in range(
        1,
        RUNS + 1,
    ):
        print(
            f"\nRun {run_number}/{RUNS}"
        )

        baseline_ms = measure_latency(
            call_ollama_direct,
            TEST_PROMPT,
        )

        guarded_ms = measure_latency(
            call_guarded,
            TEST_PROMPT,
        )

        overhead_ms = (
            guarded_ms
            - baseline_ms
        )

        baseline_latencies.append(
            baseline_ms
        )

        guarded_latencies.append(
            guarded_ms
        )

        overhead_latencies.append(
            overhead_ms
        )

        print(
            f"Direct Ollama: "
            f"{baseline_ms:.2f} ms"
        )

        print(
            f"Guarded request: "
            f"{guarded_ms:.2f} ms"
        )

        print(
            f"Observed overhead: "
            f"{overhead_ms:.2f} ms"
        )

    average_baseline = statistics.mean(
        baseline_latencies
    )

    average_guarded = statistics.mean(
        guarded_latencies
    )

    average_overhead = statistics.mean(
        overhead_latencies
    )

    median_baseline = statistics.median(
        baseline_latencies
    )

    median_guarded = statistics.median(
        guarded_latencies
    )

    median_overhead = statistics.median(
        overhead_latencies
    )

    overhead_percentage = (
        (
            average_overhead
            / average_baseline
        )
        * 100
        if average_baseline > 0
        else 0
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "Latency Summary"
    )

    print(
        "=" * 60
    )

    print(
        f"Benchmark runs: "
        f"{RUNS}"
    )

    print(
        f"Average direct latency: "
        f"{average_baseline:.2f} ms"
    )

    print(
        f"Average guarded latency: "
        f"{average_guarded:.2f} ms"
    )

    print(
        f"Average observed overhead: "
        f"{average_overhead:.2f} ms"
    )

    print(
        f"Average overhead increase: "
        f"{overhead_percentage:.1f}%"
    )

    print()

    print(
        f"Median direct latency: "
        f"{median_baseline:.2f} ms"
    )

    print(
        f"Median guarded latency: "
        f"{median_guarded:.2f} ms"
    )

    print(
        f"Median observed overhead: "
        f"{median_overhead:.2f} ms"
    )


if __name__ == "__main__":
    run_benchmark()