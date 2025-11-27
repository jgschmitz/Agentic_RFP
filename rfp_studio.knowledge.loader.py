from rfp_studio.knowledge.loader import KnowledgeItem, load_knowledge_items

items = [
    KnowledgeItem(
        text="We maintain SOC2 Type II certification with annual audits.",
        team_key="sme_team_security",
        topic="SOC2",
        tags=["security", "compliance"],
    ),
    KnowledgeItem(
        text="Our standard SLA guarantees 99.9% uptime with service credits.",
        team_key="sme_team_platform",
        topic="SLA",
        tags=["sla", "uptime"],
    ),
]

ids = load_knowledge_items(items)
print(ids)
