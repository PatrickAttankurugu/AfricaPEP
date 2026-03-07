"""GET /api/v1/pep/{id}/graph — relationship graph for D3.js/vis.js rendering."""
from fastapi import APIRouter, HTTPException
import structlog

from africapep.api.schemas import GraphResponse, GraphNode, GraphEdge
from africapep.database.neo4j_client import neo4j_client

log = structlog.get_logger()
router = APIRouter()


@router.get("/pep/{pep_id}/graph", response_model=GraphResponse)
def get_pep_graph(pep_id: str):
    """Get person + all connected nodes as JSON graph suitable for D3.js/vis.js.

    Returns nodes (person, positions, organisations, family, associates)
    and edges (relationships between them).
    """
    # Comprehensive graph query
    query = """
    MATCH (p:Person {id: $id})
    OPTIONAL MATCH (p)-[r1:HELD_POSITION]->(pos:Position)
    OPTIONAL MATCH (pos)-[:AT_ORGANISATION]->(org:Organisation)
    OPTIONAL MATCH (p)-[r2:FAMILY_OF]->(fam:Person)
    OPTIONAL MATCH (p)-[r3:ASSOCIATED_WITH]->(assoc:Person)
    OPTIONAL MATCH (p)-[:CITIZEN_OF]->(country:Country)
    OPTIONAL MATCH (p)-[:SOURCED_FROM]->(src:SourceRecord)
    RETURN p,
           collect(DISTINCT {pos: pos, held: r1}) AS positions,
           collect(DISTINCT org) AS orgs,
           collect(DISTINCT {person: fam, rel: r2}) AS family,
           collect(DISTINCT {person: assoc, rel: r3}) AS associates,
           collect(DISTINCT country) AS countries,
           collect(DISTINCT src) AS sources
    """

    results = neo4j_client.run(query, {"id": pep_id})

    if not results:
        raise HTTPException(status_code=404, detail=f"PEP not found: {pep_id}")

    record = results[0]
    person = record["p"]
    nodes = []
    edges = []
    seen_ids = set()

    # Central person node
    person_node_id = person["id"]
    nodes.append(GraphNode(
        id=person_node_id,
        label=person.get("full_name", ""),
        type="Person",
        properties={
            "pep_tier": person.get("pep_tier"),
            "is_active": person.get("is_active_pep"),
            "nationality": person.get("nationality"),
        },
    ))
    seen_ids.add(person_node_id)

    # Position nodes
    for pos_data in record.get("positions", []):
        pos = pos_data.get("pos")
        if pos and pos.get("id") and pos["id"] not in seen_ids:
            nodes.append(GraphNode(
                id=pos["id"],
                label=pos.get("title", ""),
                type="Position",
                properties={
                    "institution": pos.get("institution"),
                    "is_current": pos.get("is_current"),
                },
            ))
            seen_ids.add(pos["id"])
            edges.append(GraphEdge(
                source=person_node_id,
                target=pos["id"],
                type="HELD_POSITION",
                properties={},
            ))

    # Organisation nodes
    for org in record.get("orgs", []):
        if org and org.get("id") and org["id"] not in seen_ids:
            nodes.append(GraphNode(
                id=org["id"],
                label=org.get("name", ""),
                type="Organisation",
                properties={"org_type": org.get("org_type")},
            ))
            seen_ids.add(org["id"])

    # Family connections
    for fam_data in record.get("family", []):
        fam = fam_data.get("person")
        rel = fam_data.get("rel")
        if fam and fam.get("id") and fam["id"] not in seen_ids:
            nodes.append(GraphNode(
                id=fam["id"],
                label=fam.get("full_name", ""),
                type="Person",
                properties={"relationship": "family"},
            ))
            seen_ids.add(fam["id"])
            edges.append(GraphEdge(
                source=person_node_id,
                target=fam["id"],
                type="FAMILY_OF",
                properties={"relationship_type": rel.get("relationship_type", "") if rel else ""},
            ))

    # Associate connections
    for assoc_data in record.get("associates", []):
        assoc = assoc_data.get("person")
        rel = assoc_data.get("rel")
        if assoc and assoc.get("id") and assoc["id"] not in seen_ids:
            nodes.append(GraphNode(
                id=assoc["id"],
                label=assoc.get("full_name", ""),
                type="Person",
                properties={"relationship": "associate"},
            ))
            seen_ids.add(assoc["id"])
            edges.append(GraphEdge(
                source=person_node_id,
                target=assoc["id"],
                type="ASSOCIATED_WITH",
                properties={"relationship_type": rel.get("relationship_type", "") if rel else ""},
            ))

    # Country nodes
    for country in record.get("countries", []):
        if country and country.get("code") and country["code"] not in seen_ids:
            nodes.append(GraphNode(
                id=country["code"],
                label=country.get("name", country["code"]),
                type="Country",
                properties={"region": country.get("region")},
            ))
            seen_ids.add(country["code"])
            edges.append(GraphEdge(
                source=person_node_id,
                target=country["code"],
                type="CITIZEN_OF",
            ))

    return GraphResponse(nodes=nodes, edges=edges)
