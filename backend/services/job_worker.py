"""Job tracking and status management for background book ingestion."""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import aiosqlite

from backend.domain.entities import IngestionJob, IngestionStatus


class JobManager:
    """Persists and manages background ingestion jobs in x_ingestion_jobs."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    async def create_job(
        self,
        job_id: str,
        source_path: str,
        library_id: Optional[str] = None,
    ) -> IngestionJob:
        now = datetime.now(timezone.utc)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO x_ingestion_jobs (id, status, source_path, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (job_id, IngestionStatus.PENDING.value, source_path, now.isoformat()),
            )
            await db.commit()

        return IngestionJob(
            id=job_id,
            library_id=library_id,
            source_path=source_path,
            status=IngestionStatus.PENDING,
            created_at=now,
        )

    async def update_status(
        self,
        job_id: str,
        status: IngestionStatus,
        book_id: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE x_ingestion_jobs
                SET status = ?, book_id = ?, error_log = ?, completed_at = ?
                WHERE id = ?
                """,
                (
                    status.value,
                    book_id,
                    error_message,
                    now if status in (IngestionStatus.COMPLETED, IngestionStatus.FAILED) else None,
                    job_id,
                ),
            )
            await db.commit()

    async def get_job(self, job_id: str) -> Optional[IngestionJob]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT id, source_path, status, book_id, error_log, created_at, completed_at
                FROM x_ingestion_jobs WHERE id = ?
                """,
                (job_id,),
            ) as cur:
                row = await cur.fetchone()
                if not row:
                    return None
                return IngestionJob(
                    id=row["id"],
                    source_path=row["source_path"],
                    status=IngestionStatus(row["status"]),
                    book_id=row["book_id"],
                    error_message=row["error_log"],
                    created_at=(
                        datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
                    ),
                    completed_at=(
                        datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
                    ),
                )

    async def list_jobs(self, limit: int = 50) -> List[IngestionJob]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT id, source_path, status, book_id, error_log, created_at, completed_at
                FROM x_ingestion_jobs ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            ) as cur:
                rows = await cur.fetchall()
                jobs = []
                for row in rows:
                    jobs.append(
                        IngestionJob(
                            id=row["id"],
                            source_path=row["source_path"],
                            status=IngestionStatus(row["status"]),
                            book_id=row["book_id"],
                            error_message=row["error_log"],
                            created_at=(
                                datetime.fromisoformat(row["created_at"])
                                if row["created_at"]
                                else None
                            ),
                            completed_at=(
                                datetime.fromisoformat(row["completed_at"])
                                if row["completed_at"]
                                else None
                            ),
                        )
                    )
                return jobs
