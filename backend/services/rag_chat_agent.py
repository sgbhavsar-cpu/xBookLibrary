"""Conversational QA agent with strict grounding and verifiable citations."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from backend.domain.rag import ChatMessage, ChatSession, Citation
from backend.services.rag_search import RAGSearchService


class RAGChatAgent:
    """Manages multi-turn chat sessions and synthesizes grounded answers with citations."""

    def __init__(
        self,
        search_service: RAGSearchService,
        llm_adapter: Any = None,
        top_k: int = 5,
    ):
        self.search_service = search_service
        self.llm_adapter = llm_adapter
        self.top_k = top_k

    async def create_session(
        self,
        db: aiosqlite.Connection,
        library_id: str,
        book_id: int | None = None,
        title: str = "New Chat",
    ) -> ChatSession:
        """Initializes a new chat thread in SQLite."""
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await db.execute(
            """INSERT INTO x_chat_sessions
               (id, library_id, book_id, title, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, library_id, book_id, title, now.isoformat(), now.isoformat()),
        )
        await db.commit()

        return ChatSession(
            id=session_id,
            library_id=library_id,
            book_id=book_id,
            title=title,
            messages=[],
            created_at=now,
            updated_at=now,
        )

    async def get_session(self, db: aiosqlite.Connection, session_id: str) -> ChatSession | None:
        """Retrieves an existing chat session with its full message history."""
        query = (
            "SELECT id, library_id, book_id, title, created_at, updated_at "
            "FROM x_chat_sessions WHERE id = ?"
        )
        async with db.execute(query, (session_id,)) as cursor:
            row = await cursor.fetchone()

        if not row:
            return None

        # Fetch messages
        messages: list[ChatMessage] = []
        async with db.execute(
            "SELECT id, session_id, role, content, citations_json, created_at "
            "FROM x_chat_messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ) as msg_cursor:
            msg_rows = await msg_cursor.fetchall()

        for m in msg_rows:
            raw_cits = json.loads(m["citations_json"]) if m["citations_json"] else []
            cits = [Citation(**c) for c in raw_cits]
            created = (
                datetime.fromisoformat(m["created_at"])
                if isinstance(m["created_at"], str)
                else m["created_at"]
            )
            messages.append(
                ChatMessage(
                    id=m["id"],
                    session_id=m["session_id"],
                    role=m["role"],
                    content=m["content"],
                    citations=cits,
                    created_at=created,
                )
            )

        created_at = (
            datetime.fromisoformat(row["created_at"])
            if isinstance(row["created_at"], str)
            else row["created_at"]
        )
        updated_at = (
            datetime.fromisoformat(row["updated_at"])
            if isinstance(row["updated_at"], str)
            else row["updated_at"]
        )

        return ChatSession(
            id=row["id"],
            library_id=row["library_id"],
            book_id=row["book_id"],
            title=row["title"],
            messages=messages,
            created_at=created_at,
            updated_at=updated_at,
        )

    async def list_sessions(self, db: aiosqlite.Connection, library_id: str) -> list[ChatSession]:
        """Lists all chat threads for a given library."""
        sessions: list[ChatSession] = []
        async with db.execute(
            "SELECT id, library_id, book_id, title, created_at, updated_at "
            "FROM x_chat_sessions WHERE library_id = ? ORDER BY updated_at DESC",
            (library_id,),
        ) as cursor:
            rows = await cursor.fetchall()

        for row in rows:
            created_at = (
                datetime.fromisoformat(row["created_at"])
                if isinstance(row["created_at"], str)
                else row["created_at"]
            )
            updated_at = (
                datetime.fromisoformat(row["updated_at"])
                if isinstance(row["updated_at"], str)
                else row["updated_at"]
            )
            sessions.append(
                ChatSession(
                    id=row["id"],
                    library_id=row["library_id"],
                    book_id=row["book_id"],
                    title=row["title"],
                    messages=[],
                    created_at=created_at,
                    updated_at=updated_at,
                )
            )
        return sessions

    async def delete_session(self, db: aiosqlite.Connection, session_id: str) -> bool:
        """Deletes a chat session and associated messages."""
        cursor = await db.execute("DELETE FROM x_chat_sessions WHERE id = ?", (session_id,))
        await db.commit()
        return cursor.rowcount > 0

    async def send_message(
        self,
        db: aiosqlite.Connection,
        library_path: Path,
        session_id: str,
        user_prompt: str,
    ) -> ChatMessage:
        """Executes a conversational turn: retrieves context, prompts LLM, formats citations."""
        session = await self.get_session(db=db, session_id=session_id)
        if not session:
            raise ValueError(f"Chat session {session_id} not found")

        now = datetime.now(timezone.utc)
        user_msg_id = str(uuid.uuid4())

        # 1. Record user message
        await db.execute(
            """INSERT INTO x_chat_messages
               (id, session_id, role, content, citations_json, created_at)
               VALUES (?, ?, 'user', ?, '[]', ?)""",
            (user_msg_id, session_id, user_prompt, now.isoformat()),
        )
        await db.commit()

        # 2. Retrieve relevant context passages
        results = await self.search_service.search(
            library_path=library_path,
            query=user_prompt,
            book_id=session.book_id,
            top_k=self.top_k,
            mode="hybrid",
        )

        # 3. Grounded refusal if no context found
        if not results:
            refusal_text = (
                "I could not find information about that in the indexed books of this library."
            )
            asst_msg_id = str(uuid.uuid4())
            asst_time = datetime.now(timezone.utc)

            await db.execute(
                """INSERT INTO x_chat_messages
                   (id, session_id, role, content, citations_json, created_at)
                   VALUES (?, ?, 'assistant', ?, '[]', ?)""",
                (asst_msg_id, session_id, refusal_text, asst_time.isoformat()),
            )
            await db.execute(
                "UPDATE x_chat_sessions SET updated_at = ? WHERE id = ?",
                (asst_time.isoformat(), session_id),
            )
            await db.commit()

            return ChatMessage(
                id=asst_msg_id,
                session_id=session_id,
                role="assistant",
                content=refusal_text,
                citations=[],
                created_at=asst_time,
            )

        # 4. Assemble context block
        context_blocks = []
        for idx, r in enumerate(results, 1):
            block_header = (
                f'[{idx}] Book: "{r.book_title}" by {r.authors} | Ch: "{r.chapter_title}"'
            )
            context_blocks.append(f"{block_header}\n{r.content}\n")
        context_text = "\n---\n".join(context_blocks)

        system_instruction = (
            "You are the scholarly research assistant for xBookLibrary. "
            "Answer the user's question using ONLY the provided source passages below.\n"
            "Every factual claim MUST cite the source as [Book Title, Chapter Title].\n"
            "If the context does not contain enough information, state clearly that "
            "the answer is not present in the indexed books.\n\n"
            f"SOURCE CONTEXT:\n{context_text}"
        )

        prompt = f"User Question: {user_prompt}"

        # 5. Invoke LLM
        if self.llm_adapter:
            if hasattr(self.llm_adapter, "generate_response"):
                assistant_text = await self.llm_adapter.generate_response(
                    prompt=prompt,
                    system_instruction=system_instruction,
                )
            else:
                assistant_text = await self.llm_adapter(prompt, system_instruction)
        else:
            # Simple synthesis fallback if no LLM configured
            top_source = results[0]
            assistant_text = (
                f"Based on [{top_source.book_title}, {top_source.chapter_title}]:\n\n"
                f"{top_source.content}"
            )

        # 6. Extract citations
        citations: list[Citation] = []
        for r in results:
            prefix = f'[Book: "{r.book_title}" by {r.authors} | Chapter: "{r.chapter_title}"]'
            snippet = r.content.replace(prefix, "").strip()
            if len(snippet) > 250:
                snippet = snippet[:247] + "..."
            citations.append(
                Citation(
                    book_id=r.book_id,
                    book_title=r.book_title,
                    authors=r.authors,
                    chapter_index=r.chapter_index,
                    chapter_title=r.chapter_title,
                    snippet=snippet,
                    score=r.score,
                )
            )

        asst_msg_id = str(uuid.uuid4())
        asst_time = datetime.now(timezone.utc)
        citations_json = json.dumps([c.model_dump() for c in citations])

        await db.execute(
            """INSERT INTO x_chat_messages
               (id, session_id, role, content, citations_json, created_at)
               VALUES (?, ?, 'assistant', ?, ?, ?)""",
            (asst_msg_id, session_id, assistant_text, citations_json, asst_time.isoformat()),
        )
        await db.execute(
            "UPDATE x_chat_sessions SET updated_at = ? WHERE id = ?",
            (asst_time.isoformat(), session_id),
        )
        await db.commit()

        return ChatMessage(
            id=asst_msg_id,
            session_id=session_id,
            role="assistant",
            content=assistant_text,
            citations=citations,
            created_at=asst_time,
        )
