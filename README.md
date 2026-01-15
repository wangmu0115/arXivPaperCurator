# arXiv Paper Curator

an arXiv Paper Curator that actually solves the research discovery problem.

an elevator pitch of RAG: RAG combines search with language generation to give you contextual, accurate answers from your own knowledge base instead of generic responses.


"I'm drowning in research papers, and Google search isn't cutting it anymore."


https://jamwithai.substack.com/p/the-infrastructure-that-powers-rag


Data Ingestion: Auto-download PDFs daily from arXiv using Airflow

PDF Parsing: Extract structured content via Docling

Metadata Storage: Store authors, titles, abstracts, etc. metadata in PostgreSQL

Search Engine: Use OpenSearch with BM25 + semantic vectors (hybrid)

Chunking Engine: Evaluate different chunking

RAG Pipeline: Query expansion + retrieval + prompt templating

Local LLM: Answer questions using Ollama or API (LLaMA3, OpenAI, etc.)

Observability: Use Langfuse for prompt versioning, tracing, quality

Frontend: Ask questions and explore results via Streamlit or Gradio

FastAPI Backend: Async API server for integration and extensions

Dev Best Practices: uv, ruff, pre-commit, pydantic, pytest, logging, etc.



The gap between AI tutorials and production reality isn't the algorithms - it's the infrastructure.

For production use case, we need to make sure our systems have:

- Robust Infrastructure - Services that don't crash under load

- Clean Architecture - Code that teams can maintain and extend

- Observability - Monitoring that tells you what's actually happening

- Automation - Pipelines that run without human intervention


Build a personalized AI research assistant from scratch


https://github.com/jamwithai/arxiv-paper-curator


https://jamwithai.substack.com/p/the-mother-of-ai-project




Good Python knowledge and understanding of software programming






---

RAG Systems: Zero to Hero

  Build your own AI Research Assistant

- RAG (Retrieval-Augmented Generation)


Week 1: Infrastructure & API setup
What You'll Build:

- FastAPI skeleton project setup

- Complete Docker Compose stack orchestrating all services

- FastAPI application with health checks and basic endpoints

- PostgreSQL and OpenSearch containers with proper networking

- Ollama container for local LLM inference

- Mock data pipeline for testing without external dependencies

Key Learning Outcomes:

- Understanding microservices architecture for AI applications

- Setting up development environments with hot-reloading

- Implementing async FastAPI endpoints with proper error handling

- Container networking and service discovery

- Environment configuration and secrets management





Lesson 1: Building Your Production Foundation 构建生成基础

You're building the infrastructure backbone that every production RAG system needs. 

Complete Production Stack:

- FastAPI Backend

    - Async endpoints with comprehensive swagger documentation

    - Pydantic models for request/response validation

    - Dependency injection for database sessions

    - Error handling middleware for production reliability

    - Health check endpoints for monitoring


Build a production-grade RAG system using Docker, PostgreSQL, OpenSearch, FastAPI, Airflow, and Ollama.