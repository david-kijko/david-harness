# FastCode-Inspired Ingestion Research

**Date**: 2026-02-20
**Source**: 5 Perplexity Pro queries (Claude Sonnet 4.6)
**Raw data**: `/tmp/perplexity_fastcode_research.json`

## Key Findings Summary

### 1. FastCode Scouting-First Framework
- **Approach**: Understand structure → Navigate precisely → Load targets (NOT dump everything)
- **Performance**: 3-4x faster, 44-55% cheaper than Cursor/Claude Code, up to 10x context token reduction
- **Ships as**: MCP server (codeseys/FastCode-mcp) with 15 tools
- **Languages**: Python, TypeScript, JavaScript, Java, Go, C/C++, Rust, C#

### 2. cAST Segmentation (CMU/Augment Code)
- **Algorithm**: Recursive split-then-merge at AST node boundaries
- **Results**: +4.3 Recall@5 on RepoEval, +2.67 Pass@1 on SWE-bench vs line-based
- **Tool**: tree-sitter (language-agnostic, 40+ languages)
- **Chunk sizes**: 256-512 tokens (function), 512-1024 (class), 1024-2048 (module overview)
- **Key**: Non-whitespace char budget, NOT line count — language-invariant

### 3. Hybrid Retrieval Weighting (DKB Benchmark)
| Query Domain | AST/Graph | Semantic | BM25 |
|---|---|---|---|
| Architecture | 60% | 30% | 10% |
| Security | 35% | 25% | 40% |
| Code Quality | 20% | 50% | 30% |

- Vector-only RAG: 6/15 correct on multi-hop architecture questions
- AST-derived Graph RAG: 15/15 correct (same benchmark)
- Tree-sitter deterministic extraction is 19-45x cheaper than LLM-mediated

### 4. Context Contamination Prevention
- **Root cause**: "Semantic noise" — vectorially similar but contextually irrelevant chunks
- **Solution**: Per-subsystem source isolation (one NLM source per architectural unit)
- **Cross-cutting code**: Separate `shared-utilities` source, only included when classifier detects cross-subsystem intent
- **Query routing**: Intent classifier → metadata pre-filter → hierarchical retrieval → cross-encoder reranker

### 5. Production Pipeline (6 Stages)
1. **AST Parse** → tree-sitter per file → import graph → PageRank centrality
2. **cAST Segment** → recursive split-merge → architecturally-coherent chunks
3. **L0/L1/L2 Summaries** → LLM-generated, bottom-up (function → class → module → subsystem)
4. **Metadata Envelope** → chunk_id, source_title, arch_layer, centrality, dependencies, tags
5. **NLM Ingestion** → one source per subsystem (L1 body), per-layer notebooks
6. **Query Router** → BM25+FAISS on L0 index → dep-graph BFS expansion → grounded query

## Sources
- cAST paper: https://arxiv.org/html/2506.15655v1 (EMNLP 2025)
- CMU implementation: https://www.cs.cmu.edu/~sherryw/assets/pubs/2025-cast.pdf
- DKB benchmark: https://arxiv.org/html/2507.18515v1
- code-graph-rag: https://github.com/vitali87/code-graph-rag
- HiRAG: https://arxiv.org/html/2501.07857v1 (EMNLP 2025)
- RAGRouter: https://arxiv.org/abs/2505.23052
- Context poisoning: https://www.elastic.co/search-labs/blog/context-poisoning-llm
