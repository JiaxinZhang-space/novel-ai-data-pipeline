"""Constants deliberately fixed so repeated DEMO runs are byte-for-byte stable."""

PIPELINE_VERSION = "0.1.0"
NORMALIZATION_VERSION = "nfkc-whitespace-v1"
DATA_VERSION = "novel-demo-data-v0.1.0"
MODEL_VERSION = "template-baseline-demo-v0.1.0"
EVALUATION_VERSION = "novel-gold-demo-v0.1.0"
RIGHTS_SNAPSHOT_VERSION = "rights-demo-v0.1.0"
RUN_ID = "novel-evidence-demo-v0.1.0"
GENERATED_AT = "2026-07-16T00:00:00Z"
RIGHTS_AS_OF = "2026-07-16"
DEMO_MARKER = "DEMO_SYNTHETIC_NOT_REAL_WORLD_EVIDENCE"
DEMO_DISCLAIMER = (
    "DEMO only: all stories, users, editor events, metrics, contracts, model references, "
    "and business-like identifiers are synthetic. They are not proof of publication, "
    "usage, revenue, copyright ownership, or model performance."
)
NEAR_DUPLICATE_THRESHOLD = 0.88
MINHASH_PERMUTATIONS = 64
LSH_BANDS = 8
SHINGLE_SIZE = 5

