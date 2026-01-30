-- PostgreSQL schema for SBS error job history ingestion

create table if not exists runs (
    run_id bigserial primary key,
    base_url text not null,
    query_date date not null,
    started_at timestamptz not null default now()
);

create unique index if not exists uq_runs_baseurl_date on runs(base_url, query_date);

create table if not exists queue_stats (
    run_id bigint not null references runs(run_id) on delete cascade,
    queue_id bigint not null,
    error_count integer not null,
    primary key (run_id, queue_id)
);

create table if not exists process_stats (
    run_id bigint not null references runs(run_id) on delete cascade,
    process_name text not null,
    error_count integer not null,
    primary key (run_id, process_name)
);

create table if not exists process_queue_ids (
    run_id bigint not null references runs(run_id) on delete cascade,
    process_name text not null,
    queue_id bigint not null,
    primary key (run_id, process_name, queue_id)
);

create table if not exists process_accounts (
    run_id bigint not null references runs(run_id) on delete cascade,
    process_name text not null,
    account_id text not null,
    primary key (run_id, process_name, account_id)
);

create table if not exists log_entries (
    run_id bigint not null references runs(run_id) on delete cascade,
    log_id bigint not null,
    queue_id bigint,
    process_name text,
    message_code text,
    message text,
    created_date timestamptz,
    created_by text,
    long_text text,
    primary key (run_id, log_id)
);

create table if not exists transaction_errors (
    run_id bigint not null references runs(run_id) on delete cascade,
    process_name text not null,
    transaction_id bigint not null,
    error_count integer not null,
    primary key (run_id, process_name, transaction_id)
);

create table if not exists transaction_error_causes (
    run_id bigint not null references runs(run_id) on delete cascade,
    process_name text not null,
    transaction_id bigint not null,
    cause text not null,
    cause_count integer not null,
    primary key (run_id, process_name, transaction_id, cause)
);

create table if not exists process_error_causes (
    run_id bigint not null references runs(run_id) on delete cascade,
    process_name text not null,
    cause text not null,
    cause_count integer not null,
    primary key (run_id, process_name, cause)
);

create index if not exists idx_log_entries_process on log_entries(process_name);
create index if not exists idx_log_entries_queue on log_entries(queue_id);
create index if not exists idx_process_stats_name on process_stats(process_name);
