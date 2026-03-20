CREATE TABLE papers (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    year INTEGER CHECK (year BETWEEN 1900 AND 2100),
    doi TEXT UNIQUE,
    venue TEXT,
    source_url TEXT,
    pdf_object_key TEXT,
    full_text TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    is_airborne_sar BOOLEAN NOT NULL DEFAULT TRUE,
    is_high_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    is_high_speed BOOLEAN NOT NULL DEFAULT FALSE,
    is_large_squint BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE paper_analysis (
    id BIGSERIAL PRIMARY KEY,
    paper_id BIGINT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    entities_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    qa_cache JSONB NOT NULL DEFAULT '[]'::jsonb,
    embedding_model TEXT,
    analysis_model TEXT,
    prompt_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (paper_id)
);

CREATE TABLE paper_tags (
    id BIGSERIAL PRIMARY KEY,
    paper_id BIGINT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    tag_name TEXT NOT NULL,
    tag_category TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'openai',
    confidence NUMERIC(4, 3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE collections (
    id BIGSERIAL PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE collection_papers (
    id BIGSERIAL PRIMARY KEY,
    collection_id BIGINT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    paper_id BIGINT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (collection_id, paper_id)
);

CREATE TABLE processing_tasks (
    id BIGSERIAL PRIMARY KEY,
    paper_id BIGINT REFERENCES papers(id) ON DELETE CASCADE,
    task_name TEXT NOT NULL,
    state TEXT NOT NULL,
    provider TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_papers_year ON papers(year);
CREATE INDEX idx_papers_status ON papers(status);
CREATE INDEX idx_papers_high_speed ON papers(is_high_speed);
CREATE INDEX idx_papers_large_squint ON papers(is_large_squint);
CREATE INDEX idx_paper_tags_name ON paper_tags(tag_name);
CREATE INDEX idx_processing_tasks_state ON processing_tasks(state);

INSERT INTO collections (slug, name, description)
VALUES
    ('sar-high-speed', '高速场景 SAR 成像', '聚焦机载高分辨率 SAR 高速场景的论文集合'),
    ('sar-large-squint', '大斜视角 SAR 成像', '聚焦大斜视角机载 SAR 成像的论文集合')
ON CONFLICT (slug) DO NOTHING;
