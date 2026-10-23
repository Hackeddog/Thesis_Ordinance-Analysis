"""Label-invariant alignment and temporal sensitivity; no training or text changes."""
from __future__ import annotations
import ctypes
import os
import threading
import time

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import jensenshannon
from sklearn.metrics import adjusted_rand_score


def align_topics(left, right):
    """Hungarian maximum-sum membership Jaccard; exclude -1 and reject zero matches.

    Same ordered units required. Unmatched topics contribute zero to the symmetric
    macro score (2*sum(J)/(K_left+K_right)) and the size-weighted score. Splits/merges
    are deliberately penalized by one-to-one alignment, not equated to label failure.
    """
    a, b = np.asarray(left, dtype=int), np.asarray(right, dtype=int)
    if a.shape != b.shape or a.ndim != 1 or not len(a):
        raise ValueError("Alignment requires identical nonempty ordered units")
    ka, na = np.unique(a[a != -1], return_counts=True)
    kb, nb = np.unique(b[b != -1], return_counts=True)
    intersection = np.zeros((len(ka), len(kb)), dtype=np.int64)
    both = (a != -1) & (b != -1)
    if both.any():
        np.add.at(intersection, (np.searchsorted(ka, a[both]), np.searchsorted(kb, b[both])), 1)
    union = na[:, None] + nb[None, :] - intersection
    jaccard = np.divide(intersection, union, out=np.zeros_like(union, dtype=float), where=union > 0)
    ri, ci = linear_sum_assignment(-jaccard)
    pairs = [{"left_topic": int(ka[i]), "right_topic": int(kb[j]),
              "jaccard": float(jaccard[i, j]), "intersection": int(intersection[i, j]),
              "left_units": int(na[i]), "right_units": int(nb[j])}
             for i, j in zip(ri, ci) if jaccard[i, j] > 0]
    denom = len(ka) + len(kb)
    mass = int(na.sum() + nb.sum())
    summary = {
        "left_topics": len(ka), "right_topics": len(kb), "matched_topics": len(pairs),
        "unmatched_left_topics": len(ka) - len(pairs), "unmatched_right_topics": len(kb) - len(pairs),
        "aligned_macro_jaccard": 2 * sum(p["jaccard"] for p in pairs) / denom if denom else None,
        "aligned_weighted_jaccard": sum((p["left_units"] + p["right_units"]) * p["jaccard"] for p in pairs) / mass if mass else None,
        "matched_intersection_fraction": sum(p["intersection"] for p in pairs) / len(a),
        "ari_all_units": float(adjusted_rand_score(a, b)),
        "jointly_assigned_units": int(both.sum()),
        "ari_jointly_assigned": float(adjusted_rand_score(a[both], b[both])) if both.sum() > 1 else None,
    }
    return pd.DataFrame(pairs, columns=["left_topic", "right_topic", "jaccard", "intersection", "left_units", "right_units"]), summary


def document_prevalence(frame, labels):
    """Every document contributes total weight one; include noise and zero cells."""
    assignments = frame[["year", "ordinance_id"]].assign(topic=np.asarray(labels, dtype=int))
    per_doc = assignments.groupby(["year", "ordinance_id", "topic"]).size().rename("units").reset_index()
    per_doc["document_share"] = per_doc.units / per_doc.groupby("ordinance_id").units.transform("sum")
    observed = per_doc.groupby(["year", "topic"]).document_share.sum()
    index = pd.MultiIndex.from_product([sorted(frame.year.unique()), sorted(set(labels))], names=["year", "topic"])
    result = observed.reindex(index, fill_value=0).rename("fractional_documents").reset_index()
    result["documents_in_year"] = result.year.map(frame.groupby("year").ordinance_id.nunique())
    result["share"] = result.fractional_documents / result.documents_in_year
    return result


def temporal_comparison(frame, left, right, alignment):
    """Compare annual document-weighted distributions in aligned topic coordinates.

    Unmatched topics occupy separate bins; noise occupies a shared, explicit bin.
    JS is base-2 *divergence* (square of scipy's distance), bounded [0,1]. Equal
    weight for each observed year. This is sensitivity, not temporal ground truth.
    """
    ltab, rtab = document_prevalence(frame, left), document_prevalence(frame, right)
    right_map = {int(row.right_topic): f"L{int(row.left_topic)}" for row in alignment.itertuples()}
    ltab["bin"] = ltab.topic.map(lambda t: "noise" if t == -1 else f"L{t}")
    rtab["bin"] = rtab.topic.map(lambda t: "noise" if t == -1 else right_map.get(t, f"R{t}"))
    bins = sorted(set(ltab.bin) | set(rtab.bin))
    years = sorted(frame.year.unique())
    lp = ltab.pivot(index="year", columns="bin", values="share").reindex(index=years, columns=bins, fill_value=0).fillna(0)
    rp = rtab.pivot(index="year", columns="bin", values="share").reindex(index=years, columns=bins, fill_value=0).fillna(0)
    rows = []
    for year in years:
        p, q = lp.loc[year].to_numpy(), rp.loc[year].to_numpy()
        if not (np.isclose(p.sum(), 1) and np.isclose(q.sum(), 1)):
            raise ValueError("Annual distributions must sum to one, including noise")
        rows.append({"year": int(year), "js_divergence": float(jensenshannon(p, q, base=2) ** 2),
                     "total_variation": float(np.abs(p-q).sum()/2),
                     "left_outlier_share": float(lp.loc[year].get("noise", 0)),
                     "right_outlier_share": float(rp.loc[year].get("noise", 0))})
    # Matched-topic trajectories only; correlations cannot score missing/constant topics.
    trajectories = []
    for row in alignment.itertuples():
        p, q = lp[f"L{int(row.left_topic)}"].to_numpy(), rp[f"L{int(row.left_topic)}"].to_numpy()
        corr = float(np.corrcoef(p, q)[0, 1]) if np.std(p) > 1e-12 and np.std(q) > 1e-12 else None
        trajectories.append({"left_topic": int(row.left_topic), "right_topic": int(row.right_topic),
                             "membership_jaccard": row.jaccard, "annual_pearson": corr,
                             "annual_share_mae": float(np.abs(p-q).mean()),
                             "mean_left_share": float(p.mean()), "mean_right_share": float(q.mean())})
    annual = pd.DataFrame(rows)
    trajectory = pd.DataFrame(trajectories, columns=["left_topic", "right_topic", "membership_jaccard", "annual_pearson", "annual_share_mae", "mean_left_share", "mean_right_share"])
    valid = trajectory.dropna(subset=["annual_pearson"])
    summary = {"temporal_js_mean": float(annual.js_divergence.mean()),
               "temporal_js_max": float(annual.js_divergence.max()),
               "temporal_similarity": float(1-annual.js_divergence.mean()),
               "temporal_tv_mean": float(annual.total_variation.mean()),
               "matched_trajectory_pearson_mean": float(valid.annual_pearson.mean()) if len(valid) else None,
               "matched_trajectories_scored": len(valid)}
    return annual, trajectory, summary


def granularity(labels):
    labels = np.asarray(labels)
    sizes = pd.Series(labels[labels != -1]).value_counts()
    if sizes.empty:
        return {"largest_topic_fraction_all_units": None, "median_topic_units": None, "effective_topics": None}
    p = sizes.to_numpy() / sizes.sum()
    return {"largest_topic_fraction_all_units": float(sizes.max()/len(labels)),
            "median_topic_units": float(sizes.median()),
            "effective_topics": float(np.exp(-np.sum(p*np.log(p))))}


def _rss_bytes():
    if os.name == "nt":
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (x, ctypes.c_size_t) for x in ["PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage"]]
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return counters.WorkingSetSize
    elif os.path.exists("/proc/self/statm"):
        with open("/proc/self/statm") as handle:
            return int(handle.read().split()[1]) * os.sysconf("SC_PAGE_SIZE")
    return None


class ResourceMonitor:
    """Sample this process's resident memory, not device memory or total machine use."""
    def __enter__(self):
        self.stop = threading.Event()
        self.samples = []
        self.started = time.perf_counter()
        self.cpu = time.process_time()
        def sample():
            while not self.stop.is_set():
                try:
                    value = _rss_bytes()
                    if value is not None:
                        self.samples.append(value)
                except (OSError, AttributeError):
                    pass
                self.stop.wait(.1)
        self.thread = threading.Thread(target=sample, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.stop.set()
        self.thread.join()
        self.metrics = {"fit_evaluation_seconds": time.perf_counter()-self.started,
                        "process_cpu_seconds": time.process_time()-self.cpu,
                        "sampled_peak_rss_mib": max(self.samples)/2**20 if self.samples else None,
                        "starting_rss_mib": self.samples[0]/2**20 if self.samples else None,
                        "rss_sampling_interval_seconds": .1}
