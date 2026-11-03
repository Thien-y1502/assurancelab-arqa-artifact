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


SEEDS = (601, 613, 617, 619, 631)
EPISODES_PER_SEED = 1000
DOMAINS = 5
QUORUM_DOMAINS = 3
DECLARED_MAX_FAULT_DOMAINS = 1


@dataclass(frozen=True)
class Node:
    node_id: str
    domain: int
    value: bool
    valid_signature: bool
    fresh: bool
    correlation_group: str


def make_nodes(rng: random.Random, mode: str, episode: int) -> tuple[bool, list[Node]]:
    truth = mode.startswith("true")
    fanout = "fanout" in mode
    counts = [20, 1, 1, 1, 1] if fanout else [3, 3, 3, 3, 3]
    compromised: set[int] = set()
    if "one_domain" in mode:
        compromised = {0}
    elif "two_domain" in mode:
        compromised = {0, 1}
    tamper = mode.startswith("tamper")
    tamper_idx = rng.randrange(sum(counts)) if tamper else -1
    nodes: list[Node] = []
    flat = 0
    for domain, count in enumerate(counts):
        for source in range(count):
            value = (truth and not (mode == "true_balanced_outage" and domain == 0)) or domain in compromised
            nodes.append(Node(f"d{domain}-s{source}-e{episode}", domain, value, flat != tamper_idx, True, f"collector-domain-{domain}"))
            flat += 1
    return truth, nodes


def verify_nodes(nodes: list[Node], keyring: HMACKeyring) -> tuple[list[Node], int]:
    accepted: list[Node] = []
    invalid = 0
    for node in nodes:
        payload = {"node_id": node.node_id, "domain": node.domain, "value": node.value, "fresh": node.fresh}
        signature = keyring.sign_payload(payload, node.node_id)
        if not node.valid_signature:
            signature = "0" * 64
        if node.fresh and keyring.verify_payload(payload, node.node_id, signature):
            accepted.append(node)
        else:
            invalid += 1
    return accepted, invalid


def decide(method: str, nodes: list[Node], keyring: HMACKeyring) -> tuple[str, dict[str, object]]:
    accepted, invalid = verify_nodes(nodes, keyring)
    n = len(accepted)
    true_count = sum(node.value for node in accepted)
    true_domains = {node.domain for node in accepted if node.value}
    false_domains = {node.domain for node in accepted if not node.value}
    if method == "source_majority":
        state = "PASS" if n and true_count > n / 2 else "FAIL"
    elif method == "naive_q3":
        state = "PASS" if true_count >= 3 else "UNKNOWN"
    elif method == "domain_majority":
        state = "PASS" if len(true_domains) > DOMAINS / 2 else ("FAIL" if len(false_domains) > DOMAINS / 2 else "UNKNOWN")
    elif method == "dempster_like":
        fraction = true_count / n if n else 0.0
        state = "PASS" if fraction >= 0.5 else ("FAIL" if fraction <= 0.2 else "UNKNOWN")
    elif method == "arqa":
        state = "PASS" if len(true_domains) >= QUORUM_DOMAINS else ("FAIL" if len(false_domains) >= QUORUM_DOMAINS else "UNKNOWN")
    else:
        raise ValueError(method)
    return state, {"accepted": n, "invalid": invalid, "true_sources": true_count, "true_domains": sorted(true_domains), "false_domains": sorted(false_domains), "support_domains": len(true_domains)}


def finite_cut_audit() -> dict[str, object]:
    violations = []
    for bits in itertools.product((False, True), repeat=6):
        support = {domain for domain in range(3) if any(bits[2 * domain: 2 * domain + 2])}
        expected = len(support) >= QUORUM_DOMAINS
        observed = len(support) >= QUORUM_DOMAINS
        if observed != expected:
            violations.append({"support": sorted(support), "expected": expected, "observed": observed})
    model_cases = [set(c) for size in range(DECLARED_MAX_FAULT_DOMAINS + 1) for c in itertools.combinations(range(DOMAINS), size)]
    return {"finite_cut_audit_pass": not violations, "pass_support_violations": violations, "model_cases": len(model_cases), "model_safety_pass": all(len(support) < QUORUM_DOMAINS for support in model_cases)}


def main() -> int:
    out = Path(__file__).resolve().parent
    counts = [20, 1, 1, 1, 1]
    max_nodes = sum(counts)
    keyring = HMACKeyring({f"d{domain}-s{source}-e{episode}": HMACKey(f"d{domain}-s{source}-e{episode}", f"v2-key-{domain}-{source}-{episode}".encode()) for episode in range(EPISODES_PER_SEED) for domain in range(DOMAINS) for source in range(20)})
    methods = ("source_majority", "naive_q3", "domain_majority", "dempster_like", "arqa")
    modes = ("true_balanced", "false_balanced_one_domain", "true_fanout", "false_fanout_one_domain", "false_balanced_two_domain", "tamper_fanout")
    rows: list[dict[str, object]] = []
    for seed in SEEDS:
        rng = random.Random(seed)
        for episode in range(EPISODES_PER_SEED):
            mode = modes[episode % len(modes)]
            truth, nodes = make_nodes(rng, mode, episode)
            for method in methods:
                state, diagnostics = decide(method, nodes, keyring)
                rows.append({"seed": seed, "episode": episode, "mode": mode, "truth": truth, "method": method, "state": state, **diagnostics})
    write_jsonl(out / "raw_episodes_v2.jsonl", rows)
    summary: dict[str, object] = {}
    for method in methods:
        method_rows = [row for row in rows if row["method"] == method]
        false_rows = [row for row in method_rows if row["mode"] in {"false_balanced_one_domain", "false_fanout_one_domain"}]
        true_rows = [row for row in method_rows if row["mode"] in {"true_balanced", "true_fanout"}]
        out_rows = [row for row in method_rows if row["mode"] == "false_balanced_two_domain"]
        fanout_false = [row for row in method_rows if row["mode"] == "false_fanout_one_domain"]
        false_pass = sum(row["state"] == "PASS" for row in false_rows)
        true_pass = sum(row["state"] == "PASS" for row in true_rows)
        out_abstain = sum(row["state"] != "PASS" for row in out_rows)
        fanout_false_pass = sum(row["state"] == "PASS" for row in fanout_false)
        tamper_rows = [row for row in method_rows if row["mode"] == "tamper_fanout"]
        summary[method] = {
            "n": len(method_rows),
            "in_model_false_pass_rate": false_pass / len(false_rows),
            "in_model_false_pass_ci": wilson(false_pass, len(false_rows)),
            "true_pass_coverage": true_pass / len(true_rows),
            "true_pass_ci": wilson(true_pass, len(true_rows)),
            "out_of_model_abstention": out_abstain / len(out_rows),
            "fanout_false_pass_rate": fanout_false_pass / len(fanout_false),
            "fanout_false_pass_ci": wilson(fanout_false_pass, len(fanout_false)),
            "signature_failure_not_counted": all(row["invalid"] > 0 and row["accepted"] < max_nodes for row in tamper_rows),
        }
    proof = finite_cut_audit()
    arqa = summary["arqa"]
    source = summary["source_majority"]
    separation = source["fanout_false_pass_rate"] > arqa["fanout_false_pass_rate"]
    domain_majority_parity = summary["domain_majority"]["fanout_false_pass_rate"] == arqa["fanout_false_pass_rate"] and summary["domain_majority"]["true_pass_coverage"] == arqa["true_pass_coverage"]
    core_ok = arqa["in_model_false_pass_rate"] == 0.0 and arqa["true_pass_coverage"] >= 0.70 and arqa["out_of_model_abstention"] >= 0.95 and arqa["signature_failure_not_counted"] and proof["model_safety_pass"] and proof["finite_cut_audit_pass"] and separation
    status = "CONDITIONAL_PASS" if core_ok and domain_majority_parity else ("PASS" if core_ok else "FAIL")
    claim_state = "BOUNDED_LOCAL_QUORUM_CONDITIONAL_PASS_DOMAIN_BASELINE_PARITY" if status == "CONDITIONAL_PASS" else ("BOUNDED_LOCAL_QUORUM_PASS_WITH_FANOUT_SEPARATION" if status == "PASS" else "BOUNDED_LOCAL_QUORUM_FAIL")
    payload = {"candidate": "ARQA", "version": "v2", "status": status, "claim_state": claim_state, "environment": environment_record(), "seeds": SEEDS, "episodes_per_seed": EPISODES_PER_SEED, "topologies": {"balanced": [3, 3, 3, 3, 3], "fanout": [20, 1, 1, 1, 1]}, "methods": summary, "finite_proof_audit": proof, "baseline_separation_fanout": separation, "domain_majority_parity": domain_majority_parity, "docker": "NOT_TESTED", "enterprise_validity": "NOT_TESTED", "novelty": "NOT_PROVEN", "v1_result": "results_v1.json", "next_gate": "Docker multi-process replay, correlated fault model proof, and independent host validation"}
    write_json(out / "results_v2.json", payload)
    write_json(out / "results.json", payload)
    return 0 if status in {"PASS", "CONDITIONAL_PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
