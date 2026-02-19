from fastapi import APIRouter, Query
from services.consulta_service import buscar_por_artigo, buscar_por_tema

router = APIRouter()

@router.get("/consulta")
def consulta(
    artigo: str = Query(None), 
    tema: str = Query(None), 
    tipo: str = Query("consulta")  
):
    tipo = tipo.lower()
    if tipo not in ("consulta", "analise_situacao", "analise_contrato"):
        return {"mensagem": "Tipo inválido. Use 'consulta', 'analise_situacao' ou 'analise_contrato'."}

    if artigo:
        resultados = buscar_por_artigo(artigo, tipo=tipo)
    elif tema:
        resultados = buscar_por_tema(tema, tipo=tipo)
    else:
        return {"mensagem": "Informe pelo menos 'artigo' ou 'tema' na query."}
    
    if not resultados:
        return {"mensagem": "Nenhum resultado encontrado."}
    return resultados

