import asyncio
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiosqlite

from backend.config import ConfigManager
from backend.domain.rag import ChatMessage
from backend.providers.embedding_provider import MockEmbeddingProvider
from backend.providers.llm_adapter import LiteLLMClientAdapter
from backend.services.rag_chat_agent import RAGChatAgent
from backend.services.rag_indexer import RAGIndexer
from backend.services.rag_search import RAGSearchService
from backend.services.summarization_service import SummarizationService

sys.stdout.reconfigure(encoding="utf-8")


async def main():
    print("=" * 60)
    print("  Testing xBookLibrary with Local Ollama (qwen2.5-coder:7b)")
    print("=" * 60)

    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.load()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        print("❌ No active library configured!")
        return

    lib_path = Path(active_lib.path)
    db_file = lib_path / "metadata.db"
    print(f"📚 Active Library: {active_lib.name}")
    print(f"📁 Library Path:    {lib_path}")
    print(f"🤖 AI Provider:     {cfg.preferences.active_ai_provider}")
    print(f"🔗 Ollama Endpoint: {cfg_mgr.get_ollama_endpoint()}")
    print(f"🧠 Ollama Model:    {cfg_mgr.get_ollama_model()}")
    print("-" * 60)

    # 1. Test Direct LLM Connectivity
    print("\n[Step 1] Testing direct LiteLLM connection to Ollama...")
    llm_adapter = LiteLLMClientAdapter(config_manager=cfg_mgr)
    test_reply = await llm_adapter.generate_response(
        prompt="Introduce yourself and confirm you are ready in 1 concise sentence.",
        system_instruction="You are a helpful, professional library assistant.",
    )
    print(f"  AI Reply: {test_reply.strip()}")

    # 2. Index Book 1 (Foundation by Isaac Asimov)
    print("\n[Step 2] Indexing Book 1 ('Foundation') for RAG...")
    embedder = MockEmbeddingProvider(dimension=768)
    indexer = RAGIndexer(embedding_provider=embedder)

    async with aiosqlite.connect(str(db_file)) as db:
        db.row_factory = aiosqlite.Row
        index_res = await indexer.index_book(
            book_id=1,
            library_id=active_lib.id,
            library_path=lib_path,
            db=db,
            force=True,
        )
    print(f"  Indexing Status: {index_res.get('status')}")
    print(f"  Total Chunks:    {index_res.get('chunk_count', 0)}")

    # 3. Test RAG Search & Grounded Conversational QA
    print("\n[Step 3] Testing RAG Grounded Chat with Citations...")
    search_service = RAGSearchService(embedding_provider=embedder)
    chat_agent = RAGChatAgent(
        search_service=search_service,
        llm_adapter=llm_adapter,
        top_k=3,
    )

    async with aiosqlite.connect(str(db_file)) as db:
        db.row_factory = aiosqlite.Row
        session = await chat_agent.create_session(
            db=db,
            library_id=active_lib.id,
            book_id=1,
            title="Foundation Exploration",
        )
        print(f"  Created Chat Session ID: {session.id}")

        query = "Explain what psychohistory is and who developed it."
        print(f"  User Query: '{query}'")
        print("  Generating grounded response via Ollama...")

        msg: ChatMessage = await chat_agent.send_message(
            db=db,
            library_path=lib_path,
            session_id=session.id,
            user_prompt=query,
        )

        print("\n  === RAG Response ===")
        print(f"  {msg.content.strip()}")
        print("\n  === Citations ===")
        for idx, cit in enumerate(msg.citations, 1):
            print(f"  [{idx}] {cit.book_title} - {cit.chapter_title} (Score: {cit.score:.3f})")
            print(f"      Snippet: {cit.snippet[:120]}...")

    # 4. Test AI Multi-Resolution Summarization
    print("\n[Step 4] Testing AI Book Summarization via Ollama...")
    summarizer = SummarizationService(
        library_root=lib_path,
        config_manager=cfg_mgr,
        llm_adapter=llm_adapter,
    )

    print("  Running summarization on Book 1 ('Foundation')...")
    summary = await summarizer.summarize_book(book_id=1, force_single_pass=True, force_regenerate=True)

    print("\n  === Executive Snapshot ===")
    print(f"  Hook:           {summary.executive_snapshot.hook}")
    print(f"  Core Thesis:    {summary.executive_snapshot.core_thesis}")
    print(f"  Target Audience:{summary.executive_snapshot.target_audience}")
    print(f"  Key Arguments:  {summary.executive_snapshot.key_arguments}")

    print("\n  === Conceptual Index ===")
    print(f"  Frameworks:     {summary.conceptual_index.frameworks}")
    print(f"  Key Takeaways:  {summary.conceptual_index.key_takeaways}")
    print(f"  Action Items:   {summary.conceptual_index.action_items}")

    print("\n" + "=" * 60)
    print("  ✅ All RAG and AI Summarization tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
