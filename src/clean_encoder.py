"""Frozen Legal-BERT encoder with cross-document batching and durable checkpoints."""
import hashlib
import json
from pathlib import Path
import time

import numpy as np


def encode(docs, config, cache):
    import torch
    from transformers import AutoModel, AutoTokenizer
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    identity = {"ordered_text_sha256": hashlib.sha256(json.dumps(docs, ensure_ascii=False).encode()).hexdigest(),
                "encoder": config["encoder"], "revision": config["encoder_revision"],
                "max_tokens": config["max_tokens"], "pooling_version": "all-content-tokens-mean-v2"}
    meta_path = cache / "identity.json"
    if meta_path.exists():
        if json.loads(meta_path.read_text()) != identity:
            raise ValueError("Embedding cache identity mismatch; choose a different directory")
        if (cache / "vectors.npy").exists() and (cache / "metadata.json").exists():
            vectors = np.load(cache / "vectors.npy", allow_pickle=False)
            if vectors.ndim != 2 or len(vectors) != len(docs) or not np.isfinite(vectors).all():
                raise ValueError("Invalid completed embedding cache")
            return vectors, json.loads((cache / "metadata.json").read_text()) | {"cache_used": True}
    meta_path.write_text(json.dumps(identity, indent=2), encoding="utf-8")
    torch.manual_seed(config["seed"])
    torch.set_num_threads(min(torch.get_num_threads(), 4))
    device = config.get("device", "auto")
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA requested but unavailable; choose CPU explicitly rather than silently changing runtime")
    tokenizer = AutoTokenizer.from_pretrained(config["encoder"], revision=config["encoder_revision"], use_fast=True)
    model = AutoModel.from_pretrained(config["encoder"], revision=config["encoder_revision"]).to(device).eval()
    budget = min(config["max_tokens"], model.config.max_position_embeddings) - tokenizer.num_special_tokens_to_add(False)
    if budget < 1:
        raise ValueError("Token budget is too small")
    all_ids = tokenizer(docs, add_special_tokens=False, truncation=False, padding=False, verbose=False)["input_ids"]
    chunks, counts = [], []
    for row, ids in enumerate(all_ids):
        if not ids:
            raise ValueError(f"Empty tokenization: row {row}")
        count = 0
        for start in range(0, len(ids), budget):
            ids_chunk = ids[start:start+budget]
            # Fast-tokenizer prepare_for_model cannot create the mask; derive it after specials exist.
            prepared = tokenizer.prepare_for_model(ids_chunk, add_special_tokens=True, return_attention_mask=True,
                                                   return_special_tokens_mask=False, truncation=False)
            prepared["special_tokens_mask"] = tokenizer.get_special_tokens_mask(prepared["input_ids"], already_has_special_tokens=True)
            chunks.append((row, prepared))
            count += 1
        counts.append(count)
    sums = np.zeros((len(docs), model.config.hidden_size), dtype=np.float64)
    totals = np.zeros(len(docs), dtype=np.int64)
    next_chunk = 0
    checkpoint = cache / "checkpoint.npz"
    if checkpoint.exists():
        with np.load(checkpoint, allow_pickle=False) as prior:
            sums, totals = prior["sums"], prior["totals"]
            next_chunk = int(prior["next_chunk"])
        if sums.shape != (len(docs), model.config.hidden_size) or totals.shape != (len(docs),) or not 0 <= next_chunk <= len(chunks):
            raise ValueError("Invalid encoder checkpoint")
    resumed_at = next_chunk
    started = time.perf_counter()
    def save_checkpoint(next_index):
        temporary = cache / "checkpoint.tmp.npz"
        np.savez(temporary, sums=sums, totals=totals, next_chunk=next_index)
        temporary.replace(checkpoint)
    try:
        with torch.inference_mode():
            for start in range(next_chunk, len(chunks), config["batch_size"]):
                batch_chunks = chunks[start:start+config["batch_size"]]
                batch = tokenizer.pad([x[1] for x in batch_chunks], padding=True, return_tensors="pt")
                special = batch.pop("special_tokens_mask").to(device)
                batch = {k: v.to(device) for k, v in batch.items()}
                mask = batch["attention_mask"].bool() & ~special.bool()
                hidden = model(**batch).last_hidden_state.float()
                pooled = (hidden * mask.unsqueeze(-1)).sum(1).cpu().numpy()
                token_counts = mask.sum(1).cpu().numpy()
                for i, (row, _) in enumerate(batch_chunks):
                    sums[row] += pooled[i]
                    totals[row] += token_counts[i]
                next_chunk = start + len(batch_chunks)
                if next_chunk % 200 < config["batch_size"] or next_chunk == len(chunks):
                    print(f"BERT chunks {next_chunk}/{len(chunks)}; elapsed {time.perf_counter()-started:.1f}s", flush=True)
                    save_checkpoint(next_chunk)
    except BaseException:
        save_checkpoint(next_chunk)
        raise
    if (totals <= 0).any():
        raise ValueError("A unit has no pooled content tokens")
    vectors = sums / totals[:, None]
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if (norms <= 0).any() or not np.isfinite(vectors).all():
        raise ValueError("Invalid embedding vectors")
    vectors = (vectors / norms).astype("float32")
    metadata = {**identity, "resolved_model_revision": getattr(model.config, "_commit_hash", None),
                "device": device, "torch_version": torch.__version__, "dtype": "float32 encoder / float64 aggregation",
                "pooling": "token-weighted mean across all non-overlapping chunks, excluding padding and special tokens; L2 normalized",
                "total_chunks": len(chunks), "multi_chunk_units": sum(n > 1 for n in counts),
                "embedding_shape": list(vectors.shape), "resume_start_chunk": resumed_at,
                "session_seconds": time.perf_counter()-started, "cache_used": False}
    np.save(cache / "vectors.npy", vectors)
    (cache / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    del model
    if device == "cuda":
        torch.cuda.empty_cache()
    return vectors, metadata
