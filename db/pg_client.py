import os
from contextlib import contextmanager
from typing import Iterable, List, Tuple, Optional

import psycopg2
from psycopg2.extras import execute_values


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.environ.get(name, default)
    return value


@contextmanager
def get_conn():
    conn = psycopg2.connect(
        host=_get_env("PGHOST"),
        port=_get_env("PGPORT", "5432"),
        dbname=_get_env("PGDATABASE"),
        user=_get_env("PGUSER"),
        password=_get_env("PGPASSWORD"),
        sslmode=_get_env("PGSSLMODE", "prefer"),
    )
    try:
        yield conn
    finally:
        conn.close()


class PGClient:
    def __init__(self):
        pass

    def insert_run(self, base_url: str, query_date: str) -> int:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into runs (base_url, query_date)
                    values (%s, %s)
                    on conflict (base_url, query_date)
                    do update set base_url = excluded.base_url
                    returning run_id
                    """,
                    (base_url, query_date),
                )
                run_id = cur.fetchone()[0]
            conn.commit()
        return run_id

    def insert_queue_stats(self, run_id: int, rows: List[Tuple[int, int]]) -> None:
        if not rows:
            return
        with get_conn() as conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    insert into queue_stats (run_id, queue_id, error_count)
                    values %s
                    on conflict (run_id, queue_id)
                    do update set error_count = excluded.error_count
                    """,
                    [(run_id, queue_id, count) for queue_id, count in rows],
                )
            conn.commit()

    def insert_process_stats(self, run_id: int, rows: List[Tuple[str, int]]) -> None:
        if not rows:
            return
        with get_conn() as conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    insert into process_stats (run_id, process_name, error_count)
                    values %s
                    on conflict (run_id, process_name)
                    do update set error_count = excluded.error_count
                    """,
                    [(run_id, process_name, count) for process_name, count in rows],
                )
            conn.commit()

    def insert_process_queue_ids(self, run_id: int, rows: List[Tuple[str, int]]) -> None:
        if not rows:
            return
        with get_conn() as conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    insert into process_queue_ids (run_id, process_name, queue_id)
                    values %s
                    on conflict do nothing
                    """,
                    [(run_id, process_name, queue_id) for process_name, queue_id in rows],
                )
            conn.commit()

    def insert_process_accounts(self, run_id: int, rows: List[Tuple[str, str]]) -> None:
        if not rows:
            return
        with get_conn() as conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    insert into process_accounts (run_id, process_name, account_id)
                    values %s
                    on conflict do nothing
                    """,
                    [(run_id, process_name, account_id) for process_name, account_id in rows],
                )
            conn.commit()

    def insert_log_entries(self, run_id: int, rows: List[Tuple]) -> None:
        if not rows:
            return
        with get_conn() as conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    insert into log_entries (
                        run_id, log_id, queue_id, process_name, message_code,
                        message, created_date, created_by, long_text
                    )
                    values %s
                    on conflict do nothing
                    """,
                    [(run_id, *row) for row in rows],
                )
            conn.commit()

    def insert_transaction_errors(self, run_id: int, rows: List[Tuple[str, int, int]]) -> None:
        if not rows:
            return
        with get_conn() as conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    insert into transaction_errors (run_id, process_name, transaction_id, error_count)
                    values %s
                    on conflict (run_id, process_name, transaction_id)
                    do update set error_count = excluded.error_count
                    """,
                    [(run_id, process_name, tx_id, count) for process_name, tx_id, count in rows],
                )
            conn.commit()

    def insert_transaction_error_causes(self, run_id: int, rows: List[Tuple[str, int, str, int]]) -> None:
        if not rows:
            return
        with get_conn() as conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    insert into transaction_error_causes (run_id, process_name, transaction_id, cause, cause_count)
                    values %s
                    on conflict (run_id, process_name, transaction_id, cause)
                    do update set cause_count = excluded.cause_count
                    """,
                    [(run_id, process_name, tx_id, cause, count) for process_name, tx_id, cause, count in rows],
                )
            conn.commit()

    def insert_process_error_causes(self, run_id: int, rows: List[Tuple[str, str, int]]) -> None:
        if not rows:
            return
        with get_conn() as conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    insert into process_error_causes (run_id, process_name, cause, cause_count)
                    values %s
                    on conflict (run_id, process_name, cause)
                    do update set cause_count = excluded.cause_count
                    """,
                    [(run_id, process_name, cause, count) for process_name, cause, count in rows],
                )
            conn.commit()
