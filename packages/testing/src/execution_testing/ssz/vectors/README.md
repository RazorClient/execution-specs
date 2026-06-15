# SSZ test vectors

This directory holds SSZ static test vectors for the containers in
`execution_testing.ssz`. There are **two kinds** of vector, with different
purposes and different rules about who may produce them. Keeping them straight
is important — confusing the two re-introduces a circular test.

## 1. Cross-client reference vectors

These are **generated artifacts, not committed** — exactly like the
consensus-specs SSZ static vectors (the pyspec repo ships only the generator;
the vectors are built and released as tarballs) and EEST's own `fill` fixtures.
[`generate.py`](./generate.py) is the producer; running it writes
`<Container>/<fork>/<mode>/case_<n>.json` files for a release (the payload and
envelope are emitted per fork from the `*_BY_FORK` registries; fork-independent
containers like `Withdrawal` omit the `<fork>` segment), but the source tree
keeps none of them. Each case has the same shape the consensus-specs SSZ static
tests use:

```json
{
  "meta":       { "container": "...", "mode": "...", "seed": "0x...", ... },
  "value":      { ...consensus-spec canonical JSON... },
  "serialized": "0x...",
  "root":       "0x..."
}
```

**Producer:** `remerkleable`, via this package's adapters. **Consumers:**
independent client SSZ implementations (Nimbus, Lighthouse, Prysm, Teku,
Lodestar, the EL clients, …). This is the same arrangement as the
consensus-specs generator, whose `spec` module is the producing reference and
whose consumers are separate client implementations. Producer and consumer are
different implementations, so this is **not** circular.

For exactly that reason, this package's own correctness tests **must not**
consume these vectors as ground truth — that would be `remerkleable` checking
`remerkleable`. [`test_vectors.py`](../tests/test_vectors.py) only self-tests the
*generator*: that it is deterministic and that each emitted case's
`value`/`serialized`/`root` agree. That is a property of the generator, not a
correctness proof of the encoding.

### Determinism

Every case is seeded with `sha256(spec_version ‖ preset ‖ container ‖ mode ‖
case_index)` — never Python's `hash()`, which is salted per process. The same
tuple always yields the same value, so regeneration is reproducible across runs
and machines. The seed is recorded in each case's `meta` for auditing.

### Randomization modes

These mirror the consensus-specs `RandomizationMode`. Scalar *content* is set by
`zero`/`max`; collection *length* is set by the `*_count` modes. Modes that
randomize content emit several cases; the rest are deterministic (1 case).

- `zero` — scalars and byte vectors zeroed; collection lengths still random,
  elements zero-valued (1 case).
- `max` — scalars and byte vectors saturated; collection lengths still random,
  elements maxed (1 case).
- `nil_count` — every variable-length collection empty (1 case).
- `one_count` — exactly one element per collection, random content (several
  cases).
- `max_count` — collections filled to the cap, random content (several cases).
- `random` — random content and random collection lengths (several cases).

Note `zero`/`max` pin scalar *content* but leave collection *length* random —
emptiness and saturation of lengths are the job of `nil_count`/`max_count`.

Variable-length fields are capped (`MAX_LIST_LENGTH`, `MAX_BYTES_LENGTH` in
`generate.py`); the declared SSZ capacities — e.g. `2**30` bytes per
transaction — cannot be materialized.

### Generating

```sh
python -m execution_testing.ssz.vectors.generate
```

This writes the vector files for a release/distribution. **Do not commit the
output** — it is a generated artifact. `test_vectors.py` guards the generator
itself (determinism + per-case consistency), so it needs no committed files.

## 2. Ground-truth self-test vectors (still deferred)

Separately, the package would benefit from `*.ssz` / `*.root` vectors used to
verify **this package's own** encoding — i.e. tests where `execution_testing.ssz`
is the thing under test. Those are **still deferred**, and the rule from the
original PR stands:

> Reference vectors used to verify our own implementation are **ground truth**:
> they must be produced by an **independent** implementation, not by
> EEST/`remerkleable`, otherwise the test that consumes them is circular.

The Amsterdam `ExecutionPayload` adds two fields — `block_access_list`
(EIP-7928) and `slot_number` — that are **not yet present in the
consensus-specs reference implementation**. Until an independent oracle covers
the full Amsterdam container, canonical ground-truth vectors for it cannot be
generated. That work lands when such an oracle exists.

### Generation requirements (for the ground-truth follow-up)

When those vectors are generated, they must:

1. Be produced by an **independent** SSZ implementation (consensus-specs Python
   reference, or another non-`remerkleable` implementation), run on a known,
   committed input.
2. Pin the exact source commit(s):
   - execution-apis: `src/engine/refactor-ssz.md` @
     `4e0fed12d3ebc9d1ca8829331a82b97b1d1bd154`.
   - consensus-specs: `a84880a47a88700d8dfa451c2a7cd4b3f309bd0d` (for inherited
     Deneb/Electra fields).
3. Cover both the `minimal` and `mainnet` presets. NOTE: for these
   execution-payload size limits the two presets are identical, so the
   `ExecutionPayload` bytes and root are **byte-identical** across presets; both
   are committed regardless, matching the consensus-specs layout.
4. Exercise **multiple `transactions` of differing lengths** (≥ 3, distinct
   lengths). `transactions` is a `List[ByteList, N]`, a two-level offset
   encoding; degenerate inputs (one transaction, or all the same length) hide
   bugs in the inner offset table.
