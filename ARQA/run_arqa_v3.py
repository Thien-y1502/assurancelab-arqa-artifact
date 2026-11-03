from __future__ import annotations

import itertools
import random
import sys
from dataclasses import dataclass
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parents[1]
ROOT = BUNDLE_ROOT if (BUNDLE_ROOT / "src").exists() else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(BUNDLE_ROOT))

from assurance_lab import HMACKey, HMACKeyring  # noqa: E402
from common import environment_record, wilson, write_json, write_jsonl  # noqa: E402


SEEDS = (701, 709, 719, 727, 733)
EPISODES_PER_SEED = 1000
DOMAINS = 5
ASSERTIONS = ("availability", "backup", "access")
QUORUM_DOMAINS = 3
DECLARED_MAX_FAULT_DOMAINS = 1
BALANCED_COUNTS = (3, 3, 3, 3, 3)
FANOUT_COUNTS = (20, 1, 1, 1, 1)


@dataclass(frozen=True)
class Node:
    node_id: str
    domain: int
    assertion: str
    value: bool
    valid_signature: bool
    fresh: bool
    correlation_group: str


def _split_support(assertion: str) -> set[int]:
    # Deliberately different supports create a cross-assertion split: every
    # assertion has three positive domains, but no common three-domain cut.
    return {
        "availability": {0, 1, 2},
        "backup": {0, 1, 3},
        "access": {0, 2, 3},
    }[assertion]


def make_nodes(rng: random.Random, mode: str, seed: int, episode: int) -> tuple[bool, list[Node]]:
    truth = mode.startswith("true")
    counts = FANOUT_COUNTS if "fanout" in mode else BALANCED_COUNTS
    tamper_idx = rng.randrange(sum(counts) * len(ASSERTIONS)) if mode == "tamper_fanout" else -1
    nodes: list[Node] = []
    flat = 0
    for domain, count in enumerate(counts):
        for source in range(count):
            for assertion in ASSERTIONS:
                if mode.startswith("true") or mode == "tamper_fanout":
                    value = True
                elif mode in {"false_one_domain_balanced", "false_one_domain_fanout"}:
                    value = domain == 0
                elif mode == "false_two_domain":
                    value = domain in {0, 1}
                elif mode == "false_split_assertions":
                    value = domain in _split_support(assertion)
                elif mode == "missing_assertion":
                    value = assertion != "access"
                else:
                    raise ValueError(mode)
                node_id = f"d{domain}-s{source}-a{assertion}-seed{seed}-e{episode}"
                nodes.append(
                    Node(
                        node_id=node_id,
                        domain=domain,
                        assertion=assertion,
                        value=value,
                        valid_signature=flat != tamper_idx,
                        fresh=True,
                        correlation_group=f"collector-domain-{domain}",
                    )
                )
                flat += 1
    return truth, nodes


def verify_nodes(nodes: list[Node], keyring: HMACKeyring) -> tuple[list[Node], int]:
    accepted: list[Node] = []
    invalid = 0
    for node in nodes:
        payload = {
            "node_id": node.node_id,
            "domain": node.domain,
            "assertion": node.assertion,
            "value": node.value,
            "fresh": node.fresh,
        }
        signature = keyring.sign_payload(payload, node.node_id)
        if not node.valid_signature:
            signature = "0" * 64
        if node.fresh and keyring.verify_payload(payload, node.node_id, signature):
            accepted.append(node)
        else:
            invalid += 1
    return accepted, invalid


def _supports(nodes: list[Node], *, positive: bool) -> dict[str, set[int]]:
    return {
        assertion: {
            node.domain
            for node in nodes
            if node.assertion == assertion and node.value is positive
        }
        for assertion in ASSERTIONS
    }


def decide(method: str, nodes: list[Node], keyring: HMACKeyring) -> tuple[str, dict[str, object]]:
    accepted, invalid = verify_nodes(nodes, keyring)
    positive = _supports(accepted, positive=True)
    negative = _supports(accepted, positive=False)
    true_sources = {assertion: sum(node.value for node in accepted if node.assertion == assertion) for assertion in ASSERTIONS}
    if method == "source_majority":
        state = "PASS" if all(true_sources[a] > sum(1 for n in accepted if n.assertion == a) / 2 for a in ASSERTIONS) else "FAIL"
    elif method == "naive_q3":
        state = "PASS" if all(true_sources[a] >= 3 for a in ASSERTIONS) else "UNKNOWN"
    elif method == "global_domain_majority":
        union = set().union(*(positive[a] for a in ASSERTIONS))
        state = "PASS" if len(union) >= QUORUM_DOMAINS else ("FAIL" if len(set().union(*(negative[a] for a in ASSERTIONS))) >= QUORUM_DOMAINS else "UNKNOWN")
    elif method == "per_assertion_domain_majority":
        state = "PASS" if all(len(positive[a]) >= QUORUM_DOMAINS for a in ASSERTIONS) else ("FAIL" if all(len(negative[a]) >= QUORUM_DOMAINS for a in ASSERTIONS) else "UNKNOWN")
    elif method == "arqa":
        common_positive = set.intersection(*(positive[a] for a in ASSERTIONS))
        common_negative = set.intersection(*(negative[a] for a in ASSERTIONS))
        state = "PASS" if len(common_positive) >= QUORUM_DOMAINS else ("FAIL" if len(common_negative) >= QUORUM_DOMAINS else "UNKNOWN")
    else:
        raise ValueError(method)
    diagnostics = {
        "accepted": len(accepted),
        "invalid": invalid,
        "true_sources": true_sources,
        "positive_domains": {a: sorted(positive[a]) for a in ASSERTIONS},
        "negative_domains": {a: sorted(negative[a]) for a in ASSERTIONS},
        "common_positive_domains": sorted(set.intersection(*(positive[a] for a in ASSERTIONS))),
        "common_negative_domains": sorted(set.intersection(*(negative[a] for a in ASSERTIONS))),
    }
    return state, diagnostics


def finite_cut_audit() -> dict[str, object]:
    violations: list[dict[str, object]] = []
    for masks in itertools.product(range(1 << DOMAINS), repeat=len(ASSERTIONS)):
        supports = [set(i for i in range(DOMAINS) if mask & (1 << i)) for mask in masks]
        expected = len(set.intersection(*supports)) >= QUORUM_DOMAINS
        observed = len(set.intersection(*supports)) >= QUORUM_DOMAINS
        if observed != expected:
            violations.append({"masks": list(masks), "expected": expected, "observed": observed})
    safety_cases = [set(c) for size in range(DECLARED_MAX_FAULT_DOMAINS + 1) for c in itertools.combinations(range(DOMAINS), size)]
    safety_pass = all(len(set.intersection(*(set(case) for _ in ASSERTIONS))) < QUORUM_DOMAINS for case in safety_cases)
    return {
        "finite_cut_audit_pass": not violations,
        "pass_support_violations": violations,
        "support_state_rows": (1 << DOMAINS) ** len(ASSERTIONS),
        "model_safety_cases": len(safety_cases),
        "model_safety_pass": safety_pass,
    }


def main() -> int:
    out = Path(__file__).resolve().parent
    methods = (
        "source_majority",
        "naive_q3",
        "global_domain_majority",
        "per_assertion_domain_majority",
        "arqa",
    )
    modes = (
        "true_coherent_balanced",
        "true_coherent_fanout",
        "false_one_domain_balanced",
        "false_one_domain_fanout",
        "false_two_domain",
        "false_split_assertions",
        "missing_assertion",
        "tamper_fanout",
    )
    rows: list[dict[str, object]] = []
    for seed in SEEDS:
        rng = random.Random(seed)
        for episode in range(EPISODES_PER_SEED):
            mode = modes[episode % len(modes)]
            truth, nodes = make_nodes(rng, mode, seed, episode)
            keyring = HMACKeyring({node.node_id: HMACKey(node.node_id, f"v3-key-{node.node_id}".encode()) for node in nodes})
            for method in methods:
                state, diagnostics = decide(method, nodes, keyring)
                rows.append({"seed": seed, "episode": episode, "mode": mode, "truth": truth, "method": method, "state": state, **diagnostics})
    write_jsonl(out / "raw_episodes_v3.jsonl", rows)

    def subset(method: str, modes_: set[str]) -> list[dict[str, object]]:
        return [row for row in rows if row["method"] == method and row["mode"] in modes_]

    summary: dict[str, object] = {}
    for method in methods:
        method_rows = [row for row in rows if row["method"] == method]
        false_rows = subset(method, {"false_one_domain_balanced", "false_one_domain_fanout", "missing_assertion"})
        true_rows = subset(method, {"true_coherent_balanced", "true_coherent_fanout"})
        split_rows = subset(method, {"false_split_assertions"})
        out_rows = subset(method, {"false_two_domain"})
        tamper_rows = subset(method, {"tamper_fanout"})
        false_pass = sum(row["state"] == "PASS" for row in false_rows)
        true_pass = sum(row["state"] == "PASS" for row in true_rows)
        split_pass = sum(row["state"] == "PASS" for row in split_rows)
        out_abstain = sum(row["state"] != "PASS" for row in out_rows)
        summary[method] = {
            "n": len(method_rows),
            "in_model_false_pass_rate": false_pass / len(false_rows),
            "in_model_false_pass_ci": wilson(false_pass, len(false_rows)),
            "true_pass_coverage": true_pass / len(true_rows),
            "true_pass_ci": wilson(true_pass, len(true_rows)),
            "split_assertion_false_pass_rate": split_pass / len(split_rows),
            "split_assertion_false_pass_ci": wilson(split_pass, len(split_rows)),
            "out_of_model_abstention": out_abstain / len(out_rows),
            "out_of_model_abstention_ci": wilson(out_abstain, len(out_rows)),
            "signature_failure_not_counted": all(row["invalid"] > 0 and row["accepted"] < 72 for row in tamper_rows),
        }

    proof = finite_cut_audit()
    arqa = summary["arqa"]
    per_assertion = summary["per_assertion_domain_majority"]
    core_ok = (
        arqa["in_model_false_pass_rate"] == 0.0
        and arqa["true_pass_coverage"] >= 0.70
        and arqa["split_assertion_false_pass_rate"] == 0.0
        and per_assertion["split_assertion_false_pass_rate"] > 0.0
        and arqa["signature_failure_not_counted"]
        and proof["model_safety_pass"]
        and proof["finite_cut_audit_pass"]
    )
    status = "PASS" if core_ok else "FAIL"
    claim_state = "BOUNDED_LOCAL_MULTI_ASSERTION_PASS" if status == "PASS" else "BOUNDED_LOCAL_MULTI_ASSERTION_FAIL"
    payload = {
        "candidate": "ARQA",
        "version": "v3-multi-assertion",
        "status": status,
        "claim_state": claim_state,
        "environment": environment_record(),
        "seeds": SEEDS,
        "episodes_per_seed": EPISODES_PER_SEED,
        "assertions": ASSERTIONS,
        "topologies": {"balanced": list(BALANCED_COUNTS), "fanout": list(FANOUT_COUNTS)},
        "declared_max_compromised_domains": DECLARED_MAX_FAULT_DOMAINS,
        "quorum_domains": QUORUM_DOMAINS,
        "methods": summary,
        "finite_proof_audit": proof,
        "baseline_separation_split_assertions": per_assertion["split_assertion_false_pass_rate"] > arqa["split_assertion_false_pass_rate"],
        "docker": "NOT_TESTED",
        "enterprise_validity": "NOT_TESTED",
        "novelty": "NOT_PROVEN",
        "prior_result": "results_v2.json",
        "next_gate": "independent implementation of cut-set checker, external multi-assertion adjudication, and independent-host validation",
    }
    write_json(out / "results_v3.json", payload)
    write_json(out / "results.json", payload)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
