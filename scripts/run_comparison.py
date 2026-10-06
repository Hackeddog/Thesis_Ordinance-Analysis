"""Reproducible pilot/full experiment runner. Never overwrites prior evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare_sample(source, config):
    df = pd.read_csv(source, keep_default_na=False)
    required = {"ordinance_id", "section_id", "year", "text", "temporal_status", "verification_status"}
    if missing := required - set(df.columns):
        raise ValueError(f"Missing metadata: {sorted(missing)}")
    df["year"] = pd.to_numeric(df.year, errors="raise")
    if (df.year % 1 != 0).any():
        raise ValueError("Fractional years are invalid")
    df["year"] = df.year.astype(int)
    if df.duplicated(["ordinance_id", "section_id"]).any():
        raise ValueError("Duplicate section identifiers in source")
    if df.groupby("ordinance_id").year.nunique().gt(1).any():
        raise ValueError("Conflicting ordinance years")
    if df.text.str.strip().eq("").any():
        raise ValueError("Empty section text")
    eligible = df[df.year.isin(config["years"]) & df.temporal_status.eq("valid")].copy()
    if not config.get("allow_unverified", False):
        eligible = eligible[eligible.verification_status.eq("verified")]
    eligible = eligible.sort_values(["year", "ordinance_id", "section_id"])
    parts = []
    n = config.get("sections_per_year")
    for year in config["years"]:
        group = eligible[eligible.year.eq(year)]
        if group.empty or (n is not None and len(group) < n):
            raise ValueError(f"Year {year}: only {len(group)} eligible sections; requested {n or 'full corpus'}")
        parts.append(group.sample(n=n, random_state=config["seed"]) if n else group)
    sample = pd.concat(parts).sort_values(["year", "ordinance_id", "section_id"]).reset_index(drop=True)
    audit = []
    for year in config["years"]:
        original, available, chosen = (x[x.year.eq(year)] for x in [df, eligible, sample])
        audit.append({"year": year, "source_sections": len(original), "eligible_sections": len(available),
                      "sample_sections": len(chosen), "sample_ordinances": chosen.ordinance_id.nunique(),
                      "verified_sections": int(chosen.verification_status.eq("verified").sum())})
    return sample, pd.DataFrame(audit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/pilot.json")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    source, out = ROOT / config["source"], ROOT / config["output"]
    if out.exists():
        raise ValueError(f"Output already exists: {out}. Use a new output in the config.")
    sample, audit = prepare_sample(source, config)
    out.mkdir(parents=True)
    sample.to_csv(out / "sample.csv", index=False)
    audit.to_csv(out / "corpus_audit.csv", index=False)
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(), "config": config,
                "source_sha256": sha256(source), "sample_sha256": sha256(out / "sample.csv"),
                "model_code_sha256": sha256(ROOT / "src/model_ordinances.py"),
                "runner_code_sha256": sha256(__file__),
                "git_base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "sections": len(sample), "ordinances": sample.ordinance_id.nunique(),
                "unverified_sections": int(sample.verification_status.ne("verified").sum()),
                "duplicate_text_sections": int(sample.text.duplicated().sum()),
                "commands": [], "status": "running"}
    def save():
        (out / "experiment.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    save()
    cache = None
    all_metrics = []
    try:
        for trial in config["trials"]:
            name = trial["name"]
            settings = {**config["common"], **{k: v for k, v in trial.items() if k != "name"},
                        "seed": config["seed"], "start_year": min(config["years"]), "end_year": max(config["years"])}
            command = [sys.executable, "src/model_ordinances.py", "--input", str(out / "sample.csv"),
                       "--output", str(out / name), "--models", "both", "--skip-html"]
            for key, value in settings.items():
                command.extend(["--" + key.replace("_", "-"), str(value)])
            if cache:
                command.extend(["--semantic-cache", str(cache)])
            manifest["commands"].append(command)
            save()
            print(f"Running {name}: {len(sample)} sections, both models", flush=True)
            with (out / f"{name}.log").open("w", encoding="utf-8") as log:
                subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
            metrics = pd.read_csv(out / name / "comparison_metrics.csv")
            metrics.insert(0, "trial", name)
            for key in ["neighbors", "min_dist", "min_cluster_size", "min_samples"]:
                metrics[key] = settings[key]
            all_metrics.append(metrics)
            pd.concat(all_metrics).to_csv(out / "tuning_results.csv", index=False)
            cache = out / name / "semantic"
        manifest["status"] = "completed"
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = str(exc)
        raise
    finally:
        save()
    print(f"Completed: {out}", flush=True)


if __name__ == "__main__":
    main()
