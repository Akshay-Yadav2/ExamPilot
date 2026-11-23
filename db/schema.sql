CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE courses (
  id         text PRIMARY KEY,              -- 'daa' | 'swe' | 'ai'
  name       text NOT NULL,
  exam_date  date
);

CREATE TABLE documents (
  id          text PRIMARY KEY,             -- sha256 of the file bytes
  course_id   text NOT NULL REFERENCES courses(id),
  filename    text NOT NULL,
  path        text NOT NULL,
  pages       int,
  status      text NOT NULL DEFAULT 'queued'
              CHECK (status IN ('queued', 'processing', 'done', 'failed')),
  error       text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE topics (
  id           text PRIMARY KEY,            -- e.g. 'daa.shortest_paths'
  course_id    text NOT NULL REFERENCES courses(id),
  name         text NOT NULL,
  exam_weight  real NOT NULL DEFAULT 1.0
);

CREATE TABLE chunks (
  id           text PRIMARY KEY,            -- sha256(doc_id:page:idx)[:32]
  document_id  text NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  course_id    text NOT NULL REFERENCES courses(id),
  page         int  NOT NULL,               -- 1-based, same as the PDF viewer
  idx          int  NOT NULL,
  text         text NOT NULL,
  tokens       int  NOT NULL,
  topic_id     text REFERENCES topics(id),
  topic_conf   real,
  embed_model  text NOT NULL,
  embedding    vector(384) NOT NULL,
  tsv          tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
);
CREATE INDEX chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX chunks_tsv_gin ON chunks USING gin (tsv);
CREATE INDEX chunks_course ON chunks (course_id);
CREATE INDEX chunks_topic ON chunks (topic_id);

CREATE TABLE quiz_questions (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id          text NOT NULL REFERENCES topics(id),
  kind              text NOT NULL CHECK (kind IN ('mcq', 'short')),
  question          text NOT NULL,
  choices           jsonb NOT NULL DEFAULT '[]',
  answer            text NOT NULL,
  explanation       text NOT NULL,
  source_chunk_ids  text[] NOT NULL,
  model             text NOT NULL,
  created_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX questions_topic ON quiz_questions (topic_id);

CREATE TABLE quiz_attempts (
  id           bigserial PRIMARY KEY,
  question_id  uuid NOT NULL REFERENCES quiz_questions(id),
  user_answer  text NOT NULL,
  score        smallint NOT NULL,
  max_score    smallint NOT NULL,
  feedback     text,
  answered_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX attempts_question_time ON quiz_attempts (question_id, answered_at DESC);

-- Beta(alpha, beta) per topic for the scheduler
CREATE TABLE topic_stats (
  topic_id    text PRIMARY KEY REFERENCES topics(id),
  alpha       real NOT NULL DEFAULT 1.0,
  beta        real NOT NULL DEFAULT 1.0,
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE reviews (
  question_id    uuid PRIMARY KEY REFERENCES quiz_questions(id),
  due_at         timestamptz NOT NULL,
  interval_days  real NOT NULL,
  ease           real NOT NULL DEFAULT 2.5,
  reps           int  NOT NULL DEFAULT 0
);
CREATE INDEX reviews_due ON reviews (due_at);

CREATE TABLE llm_calls (
  id                 bigserial PRIMARY KEY,
  kind               text NOT NULL,         -- chat | quiz_gen | grade | label | judge
  model              text NOT NULL,
  input_tokens       int NOT NULL,
  output_tokens      int NOT NULL,
  cache_read_tokens  int NOT NULL DEFAULT 0,
  cache_write_tokens int NOT NULL DEFAULT 0,
  latency_ms         int NOT NULL,
  cost_usd           numeric(10, 6) NOT NULL,
  stop_reason        text,
  request_id         text,
  created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE chat_messages (
  conversation_id  uuid NOT NULL,
  seq              int  NOT NULL,
  role             text NOT NULL CHECK (role IN ('user', 'assistant')),
  content          jsonb NOT NULL,          -- exact blocks, so the cache prefix stays identical
  created_at       timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (conversation_id, seq)
);

INSERT INTO courses (id, name, exam_date) VALUES
  ('swe', 'Software Engineering', '2026-12-16'),
  ('ai',  'Artificial Intelligence', '2026-12-17'),
  ('daa', 'Design and Analysis of Algorithms', '2026-12-21');
