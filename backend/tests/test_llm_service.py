import json

from backend.app.core.enums import ResponseMode, SourceAuthority, SourceType
from backend.app.core.text import stable_id
from backend.app.models.domain import Citation, ChunkRecord, RetrievedChunk, SourceMetadata
from backend.app.services.llm_service import LegalLLMService


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeChatModel:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)

    def invoke(self, _messages):
        return FakeMessage(self._responses.pop(0))


def test_generate_answer_appends_verification_issues():
    service = LegalLLMService()
    service.provider = "google"
    service.chat_model = FakeChatModel(
        [
            json.dumps(
                {
                    "resposta_objetiva": "O contexto fala apenas do art. 473 da CLT.",
                    "fundamentacao_juridica": "A base recuperada menciona apenas o art. 473.",
                    "limites": [],
                    "proximos_passos": ["Conferir a versao vigente da CLT."],
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "verified": False,
                    "issues": ["A resposta final menciona suporte para art. 999, mas esse artigo nao aparece nas fontes recuperadas."],
                },
                ensure_ascii=False,
            ),
        ]
    )

    metadata = SourceMetadata(numero_norma="CLT", artigo="473")
    chunk = ChunkRecord(
        chunk_id=stable_id("chunk", "clt", "473"),
        source_id="source-clt-473",
        document_id="doc-clt-473",
        version_id="ver-clt-473",
        title="Consolidacao das Leis do Trabalho",
        content="Art. 473. O empregado podera deixar de comparecer ao servico em hipoteses legais.",
        hierarchy=["art. 473"],
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        metadata=metadata,
        hash=stable_id("hash", "clt", "473"),
        search_text="CLT art. 473 empregado comparecer servico",
    )
    retrieved = [
        RetrievedChunk(
            chunk=chunk,
            vector_score=0.8,
            lexical_score=0.7,
            rerank_score=0.6,
            final_score=0.82,
            reason="artigo exato",
        )
    ]
    citations = [
        Citation(
            citation_id=chunk.chunk_id,
            chunk_id=chunk.chunk_id,
            source_id=chunk.source_id,
            title=chunk.title,
            source_type=chunk.source_type,
            authority=chunk.authority,
            quote=chunk.content[:120],
            reference_label="Consolidacao das Leis do Trabalho | art. 473",
            metadata={"artigo": "473"},
        )
    ]

    generated = service.generate_answer(
        question="O que diz o art. 473 da CLT?",
        mode=ResponseMode.TECHNICAL,
        retrieved=retrieved,
        citations=citations,
        limitations=[],
    )

    assert generated.verification.executed is True
    assert generated.verification.verified is False
    assert any("art. 999" in issue for issue in generated.limitations)
