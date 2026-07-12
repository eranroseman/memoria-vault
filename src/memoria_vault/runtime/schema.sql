-- Memoria runtime SQLite schema. Applied by runtime.state via PRAGMA user_version.
CREATE TABLE IF NOT EXISTS operation_requests (
    request_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    args_json TEXT NOT NULL DEFAULT '{}',
    idempotency_key TEXT UNIQUE,
    input_refs_json TEXT NOT NULL DEFAULT '[]',
    output_intents_json TEXT NOT NULL DEFAULT '[]',
    primary_target TEXT NOT NULL DEFAULT '',
    precondition_hashes_json TEXT NOT NULL DEFAULT '{}',
    causal_refs_json TEXT NOT NULL DEFAULT '[]',
    actor TEXT NOT NULL CHECK (actor IN ('pi', 'agent', 'operation', 'integrity')),
    provenance_json TEXT NOT NULL DEFAULT '{}',
    schedule_id TEXT,
    status TEXT NOT NULL
        CHECK (status IN ('pending', 'running', 'done', 'failed', 'cancelled')),
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    kind TEXT NOT NULL DEFAULT 'operation',
    job_json TEXT NOT NULL,
    error TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_operation_requests_status
    ON operation_requests(status, created_at);

CREATE TABLE IF NOT EXISTS event_log (
    event_id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    machine TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    row_hash TEXT NOT NULL UNIQUE
);
CREATE TRIGGER IF NOT EXISTS event_log_no_update
BEFORE UPDATE ON event_log
BEGIN
    SELECT RAISE(ABORT, 'journal is append-only');
END;
CREATE TRIGGER IF NOT EXISTS event_log_no_delete
BEFORE DELETE ON event_log
BEGIN
    SELECT RAISE(ABORT, 'journal is append-only');
END;
CREATE INDEX IF NOT EXISTS idx_event_log_event_type
    ON event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_event_log_timestamp
    ON event_log(timestamp);

CREATE TABLE IF NOT EXISTS concepts (
    concept_id TEXT PRIMARY KEY,
    concept_type TEXT NOT NULL
        CHECK (concept_type IN (
            'work', 'digest', 'note', 'hub', 'project', 'capability',
            'operation', 'skill', 'adapter', 'workflow'
        )),
    store TEXT NOT NULL CHECK (store IN ('db', 'file'))
);
CREATE TABLE IF NOT EXISTS concept_verdicts (
    concept_id TEXT PRIMARY KEY,
    check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined'))
);
CREATE TABLE IF NOT EXISTS concept_flags (
    concept_id TEXT NOT NULL,
    flag TEXT NOT NULL CHECK (flag IN ('stale')),
    reason TEXT NOT NULL DEFAULT '',
    trigger_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    PRIMARY KEY (concept_id, flag)
);
CREATE VIEW IF NOT EXISTS concept_status AS
SELECT
    c.concept_id,
    c.concept_type,
    c.store,
    COALESCE(v.check_status, 'unchecked') AS check_status
FROM concepts c
LEFT JOIN concept_verdicts v ON v.concept_id = c.concept_id;
CREATE TABLE IF NOT EXISTS outputs (
    output_id TEXT PRIMARY KEY,
    concept_type TEXT NOT NULL,
    store TEXT NOT NULL CHECK (store IN ('db', 'file')),
    target_path TEXT NOT NULL,
    staging_path TEXT NOT NULL DEFAULT '',
    check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
    materialization_status TEXT NOT NULL
        CHECK (materialization_status IN ('none', 'pending', 'materialized', 'failed')),
    output_sha256 TEXT NOT NULL DEFAULT '',
    materialized_commit TEXT NOT NULL DEFAULT '',
    failure_reason TEXT
);
CREATE TABLE IF NOT EXISTS materialization_payloads (
    output_id TEXT PRIMARY KEY REFERENCES outputs(output_id) ON DELETE CASCADE,
    expected_sha256 TEXT NOT NULL,
    payload_text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS catalog_sources (
    work_id TEXT PRIMARY KEY,
    concept_path TEXT NOT NULL,
    doi TEXT UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    resource TEXT NOT NULL DEFAULT '',
    item_type TEXT NOT NULL DEFAULT 'article',
    identifiers_json TEXT NOT NULL DEFAULT '{}',
    citekey TEXT NOT NULL DEFAULT '',
    csl_json TEXT NOT NULL DEFAULT '{}',
    provider_coverage TEXT NOT NULL CHECK (provider_coverage IN ('full', 'partial', 'degraded')),
    text_status TEXT NOT NULL
        CHECK (text_status IN ('full-text', 'abstract-only', 'metadata-only')),
    check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
    content_hash TEXT NOT NULL DEFAULT '',
    raw_hash TEXT NOT NULL DEFAULT '',
    content_path TEXT NOT NULL DEFAULT '',
    raw_path TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS external_ids (
    owner_type TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    namespace TEXT NOT NULL,
    value TEXT NOT NULL,
    source_provider TEXT NOT NULL DEFAULT '',
    confidence TEXT NOT NULL DEFAULT 'high',
    verified_at TEXT NOT NULL,
    PRIMARY KEY (owner_type, owner_id, namespace, value)
);
CREATE TABLE IF NOT EXISTS enrichment_runs (
    run_id TEXT PRIMARY KEY,
    work_id TEXT NOT NULL,
    enrichment_status TEXT NOT NULL
        CHECK (
            enrichment_status IN (
                'pending', 'enriched', 'partial', 'failed', 'needs_human', 'contested'
            )
        ),
    required_provider_policy_json TEXT NOT NULL DEFAULT '{}',
    started_at TEXT NOT NULL,
    finished_at TEXT,
    request_id TEXT NOT NULL DEFAULT '',
    event_id TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS provider_payloads (
    payload_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    request_key TEXT NOT NULL,
    request_params_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    raw_hash TEXT NOT NULL,
    raw_path TEXT NOT NULL,
    normalized_json TEXT NOT NULL DEFAULT '{}',
    error TEXT NOT NULL DEFAULT '',
    latency_ms INTEGER NOT NULL DEFAULT 0,
    retry_count INTEGER NOT NULL DEFAULT 0,
    ttl_until TEXT NOT NULL DEFAULT '',
    UNIQUE(run_id, provider, request_key, request_params_hash)
);
CREATE TABLE IF NOT EXISTS field_provenance (
    work_id TEXT NOT NULL,
    field_path TEXT NOT NULL,
    value_hash TEXT NOT NULL,
    winning_provider TEXT NOT NULL,
    evidence_payload_id TEXT NOT NULL DEFAULT '',
    alternatives_json TEXT NOT NULL DEFAULT '[]',
    confidence TEXT NOT NULL DEFAULT 'high',
    conflict_status TEXT NOT NULL DEFAULT 'none',
    PRIMARY KEY (work_id, field_path)
);
CREATE TABLE IF NOT EXISTS work_graph_edges (
    work_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK (
        relation_type IN (
            'references', 'related', 'topic', 'keyword',
            'authorship', 'institution', 'published_in'
        )
    ),
    target_id TEXT NOT NULL,
    target_title TEXT NOT NULL DEFAULT '',
    target_doi TEXT NOT NULL DEFAULT '',
    source_provider TEXT NOT NULL DEFAULT '',
    raw_json TEXT NOT NULL DEFAULT '{}',
    discovered_at TEXT NOT NULL,
    PRIMARY KEY (work_id, relation_type, target_id)
);
CREATE TABLE IF NOT EXISTS work_aspects (
    work_id TEXT NOT NULL,
    aspect_type TEXT NOT NULL CHECK (
        aspect_type IN ('context', 'key_idea', 'method', 'outcome', 'limitation', 'assumption')
    ),
    aspect_text TEXT NOT NULL,
    anchor_text TEXT NOT NULL DEFAULT '',
    check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
    source_provider TEXT NOT NULL DEFAULT 'deterministic',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (work_id, aspect_type)
);
CREATE TABLE IF NOT EXISTS passages (
    passage_id TEXT PRIMARY KEY,
    origin TEXT NOT NULL CHECK (origin IN ('file', 'generated')),
    concept_id TEXT NOT NULL DEFAULT '',
    work_id TEXT NOT NULL DEFAULT '',
    path TEXT NOT NULL,
    anchor TEXT NOT NULL DEFAULT '',
    page TEXT NOT NULL DEFAULT '',
    byte_start INTEGER NOT NULL DEFAULT 0,
    byte_end INTEGER NOT NULL DEFAULT 0,
    text_sha256 TEXT NOT NULL,
    text TEXT NOT NULL,
    check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
    mode TEXT NOT NULL DEFAULT '',
    question_status TEXT NOT NULL DEFAULT '',
    source_mtime_ns INTEGER NOT NULL DEFAULT 0,
    indexed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_passages_path_status
    ON passages(path, check_status);
CREATE INDEX IF NOT EXISTS idx_passages_work_status
    ON passages(work_id, check_status);
CREATE VIRTUAL TABLE IF NOT EXISTS passage_fts
USING fts5(passage_id UNINDEXED, text);
CREATE TABLE IF NOT EXISTS passage_vec (
    passage_id TEXT PRIMARY KEY,
    text_sha256 TEXT NOT NULL,
    embedding_model_id TEXT NOT NULL,
    vector_dim INTEGER NOT NULL,
    distance_metric TEXT NOT NULL DEFAULT 'cosine' CHECK (distance_metric = 'cosine'),
    vector_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (passage_id) REFERENCES passages(passage_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS file_index_state (
    path TEXT PRIMARY KEY,
    source_mtime_ns INTEGER NOT NULL DEFAULT 0,
    source_sha256 TEXT NOT NULL DEFAULT '',
    check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
    indexed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS concept_edges (
    source_concept_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK (
        relation_type IN ('supports', 'contradicts', 'extends', 'tension')
    ),
    target_concept_id TEXT NOT NULL,
    check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
    source_path TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (source_concept_id, relation_type, target_concept_id)
);
CREATE TRIGGER IF NOT EXISTS concept_verdicts_passage_cascade_insert
AFTER INSERT ON concept_verdicts
BEGIN
    UPDATE passages
    SET check_status = NEW.check_status
    WHERE concept_id = NEW.concept_id
       OR path = NEW.concept_id
       OR ('catalog/sources/' || work_id) = NEW.concept_id;
END;
CREATE TRIGGER IF NOT EXISTS concept_verdicts_passage_cascade_update
AFTER UPDATE OF check_status ON concept_verdicts
BEGIN
    UPDATE passages
    SET check_status = NEW.check_status
    WHERE concept_id = NEW.concept_id
       OR path = NEW.concept_id
       OR ('catalog/sources/' || work_id) = NEW.concept_id;
END;
CREATE TRIGGER IF NOT EXISTS catalog_sources_passage_cascade_update
AFTER UPDATE OF check_status ON catalog_sources
BEGIN
    UPDATE passages
    SET check_status = NEW.check_status
    WHERE work_id = NEW.work_id
       OR concept_id = ('catalog/sources/' || NEW.work_id);
END;
CREATE TRIGGER IF NOT EXISTS passage_fts_insert
AFTER INSERT ON passages
BEGIN
    INSERT INTO passage_fts(rowid, passage_id, text)
    VALUES (NEW.rowid, NEW.passage_id, NEW.text);
END;
CREATE TRIGGER IF NOT EXISTS passage_fts_delete
AFTER DELETE ON passages
BEGIN
    DELETE FROM passage_fts WHERE rowid = OLD.rowid;
END;
CREATE TRIGGER IF NOT EXISTS passage_fts_update
AFTER UPDATE OF text, passage_id ON passages
BEGIN
    DELETE FROM passage_fts WHERE rowid = OLD.rowid;
    INSERT INTO passage_fts(rowid, passage_id, text)
    VALUES (NEW.rowid, NEW.passage_id, NEW.text);
END;
CREATE TABLE IF NOT EXISTS code_artifacts (
    artifact_id TEXT PRIMARY KEY,
    project_path TEXT NOT NULL,
    record_path TEXT NOT NULL UNIQUE,
    source_dir TEXT NOT NULL,
    output_dir TEXT NOT NULL,
    purpose TEXT NOT NULL CHECK (purpose IN ('warrant', 'deliverable', 'both')),
    approved_command_json TEXT NOT NULL DEFAULT '[]',
    declared_inputs_json TEXT NOT NULL DEFAULT '[]',
    declared_outputs_json TEXT NOT NULL DEFAULT '[]',
    dependency_notes TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('draft', 'ready', 'failed', 'retired')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS code_runs (
    run_id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL REFERENCES code_artifacts(artifact_id) ON DELETE CASCADE,
    command_json TEXT NOT NULL,
    cwd TEXT NOT NULL,
    sanitized_env_json TEXT NOT NULL DEFAULT '[]',
    input_hashes_json TEXT NOT NULL DEFAULT '{}',
    output_hashes_json TEXT NOT NULL DEFAULT '{}',
    stdout_sha256 TEXT NOT NULL DEFAULT '',
    stderr_sha256 TEXT NOT NULL DEFAULT '',
    stdout_path TEXT NOT NULL DEFAULT '',
    stderr_path TEXT NOT NULL DEFAULT '',
    exit_status INTEGER,
    timeout_result TEXT NOT NULL DEFAULT '',
    sandbox_backend TEXT NOT NULL DEFAULT '',
    sandbox_profile_hash TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL CHECK (state IN ('pending', 'running', 'succeeded', 'failed', 'unavailable')),
    started_at TEXT NOT NULL,
    ended_at TEXT
);
CREATE TABLE IF NOT EXISTS evidence_sets (
    id TEXT PRIMARY KEY,
    block_ref TEXT NOT NULL,
    items_json TEXT NOT NULL DEFAULT '[]',
    type TEXT NOT NULL CHECK (
        type IN ('single-span', 'multi-span', 'multi-hop', 'implicit', 'computed')
    ),
    state TEXT NOT NULL CHECK (state IN ('complete', 'evidence-incomplete')),
    review_required INTEGER NOT NULL CHECK (review_required IN (0, 1)),
    run_id TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_evidence_sets_block_ref
    ON evidence_sets(block_ref);
CREATE TABLE IF NOT EXISTS derivations (
    input_id TEXT NOT NULL,
    output_id TEXT NOT NULL,
    actor TEXT NOT NULL CHECK (actor IN ('pi', 'agent', 'operation', 'integrity')),
    PRIMARY KEY (input_id, output_id)
);
CREATE VIEW IF NOT EXISTS consumable_outputs AS
SELECT output_id, concept_type, store, target_path, output_sha256
FROM outputs
WHERE check_status = 'checked'
  AND (
    store = 'db'
    OR (store = 'file' AND materialization_status = 'materialized')
  );
PRAGMA user_version = 9;
