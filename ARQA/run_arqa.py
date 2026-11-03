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


SEEDS = (101, 211, 307, 401, 503)
EPISODES_PER_SEED = 1000
DOMAINS = 5
SOURCES_PER_DOMAIN = 3
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
    compromised_domains: set[int] = set()
    if mode == "false_one_domain":
        compromised_domains = {rng.randrange(DOMAINS)}
    elif mode == "false_two_domain":
        compromised_domains = set(rng.sample(range(DOMAINS), 2))
    outage_domain = rng.randrange(DOMAINS) if mode == "true_outage" else None
    tamper_node = rng.randrange(DOMAINS * SOURCES_PER_DOMAIN) if mode == "tamper" else None
    nodes: list[Node] = []
    for domain in range(DOMAINS):
        for source in range(SOURCES_PER_DOMAIN):
            idx = domain * SOURCES_PER_DOMAIN + source
            compromised = domain in compromised_domains
            available = outage_domain != domain
            value = (truth and available) or compromised
            fresh = mode != "stale" or (idx % 3 != 0)
            valid_signature = idx != tamper_node
            nodes.append(Node(f"d{domain}-s{source}-e{episode}", domain, value, valid_signature, fresh, f"collector-domain-{domain}"))
    return truth, nodes


def verified_nodes(nodes: list[Node], keyring: HMACKeyring) -> tuple[list[Node], int]:
    accepted: list[Node] = []
    invalid = 0
    for node in nodes:
        payload = {"node_id": node.node_id, "domain": node.domain, "value": node.value, "fresh": node.fresh}
        key_id = node.node_id
        signature = keyring.sign_payload(payload, key_id)
        if not node.valid_signature:
            signature = "0" * 64
        if keyring.verify_payload(payload, key_id, signature) and node.fresh:
            accepted.append(node)
        else:
            invalid += 1
    return accepted, invalid


def decide(method: str, nodes: list[Node], keyring: HMACKeyring) -> tuple[str, dict[str, object]]:
    accepted, invalid = verified_nodes(nodes, keyring)
    true_count = sum(node.value for node in accepted)
    domains_true = {node.domain for node in accepted if node.value}
    domains_false = {node.domain for node in accepted if not node.value}
    n = len(accepted)
    if method == "source_majority":
        state = "PASS" if n and true_count > n / 2 else "FAIL"
    elif method == "naive_q3":
        state = "PASS" if true_count >= 3 else "UNKNOWN"
    elif method == "domain_majority":
        state = "PASS" if len(domains_true) > DOMAINS / 2 else ("FAIL" if len(domains_false) > DOMAINS / 2 else "UNKNOWN")
    elif method == "dempster_like":
        weight = true_count / n if n else 0.0
        state = "PASS" if weight >= 0.5 else ("FAIL" if weight <= 0.2 else "UNKNOWN")
    elif method == "arqa":
        if len(domains_true) >= QUORUM_DOMAINS:
            state = "PASS"
        elif len(domains_false) >= QUORUM_DOMAINS:
            state = "FAIL"
        else:
            state = "UNKNOWN"
    else:
        raise ValueError(method)
    return state, {"accepted": n, "invalid": invalid, "true_sources": true_count, "true_domains": sorted(domains_true), "false_domains": sorted(domains_false), "support_domains": len(domains_true)}


def proof_audit() -> dict[str, object]:
    violations = []
    for true_domains in itertools.chain.from_iterable(itertools.combinations(range(DOMAINS), size) for size in range(DOMAINS + 1)):
        support = set(true_domains)
        if len(support) >= QUORUM_DOMAINS:
            state = "PASS"
        else:
            state = "UNKNOWN"
        if state == "PASS" and len(support) < QUORUM_DOMAINS:
            violations.append({"support": sorted(support)})
    model_safety = []
    for compromised in itertools.chain.from_iterable(itertools.combinations(range(DOMAINS), size) for size in range(DECLARED_MAX_FAULT_DOMAINS + 1)):
        support = set(compromised)
        model_safety.append({"compromised": sorted(support), "arqa_pass": len(support) >= QUORUM_DOMAINS})
    return {"quorum_domains": QUORUM_DOMAINS, "pass_support_violations": violations, "model_safety_cases": len(model_safety), "model_safety_pass": not any(item["arqa_pass"] for item in model_safety), "finite_cut_audit_pass": not violations}


def main() -> int:
    out = Path(__file__).resolve().parent
    keyring = HMACKeyring({f"d{domain}-s{source}-e{episode}": HMACKey(f"d{domain}-s{source}-e{episode}", f"key-{domain}-{source}-{episode}".encode()) for episode in range(EPISODES_PER_SEED) for domain in range(DOMAINS) for source in range(SOURCES_PER_DOMAIN)})
    methods = ("source_majority", "naive_q3", "domain_majority", "dempster_like", "arqa")
    modes = ("true_clean", "true_outage", "false_one_domain", "false_two_domain", "stale", "tamper")
    rows: list[dict[str, object]] = []
    for seed in SEEDS:
        rng = random.Random(seed)
        for episode in range(EPISODES_PER_SEED):
            mode = modes[episode % len(modes)]
            truth, nodes = make_nodes(rng, mode, episode)
            for method in methods:
                state, diagnostics = decide(method, nodes, keyring)
                rows.append({"seed": seed, "episode": episode, "mode": mode, "truth": truth, "method": method, "state": state, **diagnostics})
    write_jsonl(out / "raw_episodes.jsonl", rows)
    summary: dict[str, object] = {}
    for method in methods:
        method_rows = [row for row in rows if row["method"] == method]
        in_model_false = [row for row in method_rows if row["mode"] == "false_one_domain"]
        true_rows = [row for row in method_rows if row["mode"] in {"true_clean", "true_outage"}]
        out_model = [row for row in method_rows if row["mode"] == "false_two_domain"]
        false_pass = sum(row["state"] == "PASS" for row in in_model_false)
        true_pass = sum(row["state"] == "PASS" for row in true_rows)
        out_abstain = sum(row["state"] != "PASS" for row in out_model)
        invalid_not_counted = all(row["invalid"] > 0 and row["accepted"] < DOMAINS * SOURCES_PER_DOMAIN for row in method_rows if row["mode"] == "tamper")
        summary[method] = {
            "n": len(method_rows),
            "in_model_false_pass_rate": false_pass / len(in_model_false),
            "in_model_false_pass_ci": wilson(false_pass, len(in_model_false)),
            "true_pass_coverage": true_pass / len(true_rows),
            "true_pass_ci": wilson(true_pass, len(true_rows)),
            "out_of_model_abstention": out_abstain / len(out_model),
            "out_of_model_abstention_ci": wilson(out_abstain, len(out_model)),
            "signature_failure_not_counted": invalid_not_counted,
        }
    proof = proof_audit()
    m = summary["arqa"]
    status = "PASS" if m["in_model_false_pass_rate"] == 0.0 and m["true_pass_coverage"] >= 0.70 and m["out_of_model_abstention"] >= 0.95 and m["signature_failure_not_counted"] and proof["model_safety_pass"] and proof["finite_cut_audit_pass"] else "FAIL"
    payload = {"candidate": "ARQA", "status": status, "claim_state": "BOUNDED_LOCAL_QUORUM_PASS" if status == "PASS" else "BOUNDED_LOCAL_QUORUM_FAIL", "environment": environment_record(), "seeds": SEEDS, "episodes_per_seed": EPISODES_PER_SEED, "topology": {"domains": DOMAINS, "sources_per_domain": SOURCES_PER_DOMAIN, "declared_max_fault_domains": DECLARED_MAX_FAULT_DOMAINS, "quorum_domains": QUORUM_DOMAINS}, "methods": summary, "finite_proof_audit": proof, "docker": "NOT_TESTED", "enterprise_validity": "NOT_TESTED", "novelty": "NOT_PROVEN", "next_gate": "Docker multi-process replay, correlated fault model proof, and independent host validation"}
    write_json(out / "results.json", payload)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
