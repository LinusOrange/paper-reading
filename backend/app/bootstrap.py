from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Paper, PaperAnalysis, PaperTag, ProcessingTask


def ensure_demo_data(db: Session) -> None:
    existing = db.scalar(select(Paper.id).limit(1))
    if existing:
        return

    papers = [
        Paper(
            title="Large-Squint Airborne SAR Imaging Demo Paper",
            abstract="Demo seed paper for large-squint SAR imaging.",
            year=2024,
            doi="10.0000/demo",
            venue="Demo Venue",
            source_url="https://example.org/paper",
            pdf_object_key="papers/demo.pdf",
            full_text="Seed text for large-squint airborne SAR imaging.",
            status="analyzed",
            is_large_squint=True,
        ),
        Paper(
            title="High-Speed Airborne SAR Imaging Demo Paper",
            abstract="Demo seed paper for high-speed airborne SAR imaging.",
            year=2023,
            doi="10.0000/highspeed",
            venue="IEEE Demo",
            source_url="https://example.org/highspeed",
            pdf_object_key="papers/highspeed.pdf",
            full_text="Seed text for high-speed airborne SAR imaging.",
            status="reviewed",
            is_high_speed=True,
        ),
    ]
    db.add_all(papers)
    db.flush()

    db.add_all(
        [
            PaperTag(paper_id=papers[0].id, tag_name="airborne-sar", tag_category="topic", source="seed"),
            PaperTag(paper_id=papers[0].id, tag_name="large-squint", tag_category="topic", source="seed"),
            PaperTag(paper_id=papers[1].id, tag_name="airborne-sar", tag_category="topic", source="seed"),
            PaperTag(paper_id=papers[1].id, tag_name="high-speed", tag_category="topic", source="seed"),
        ]
    )

    db.add_all(
        [
            PaperAnalysis(
                paper_id=papers[0].id,
                summary_json={
                    "problem": "Improve large-squint airborne SAR imaging quality.",
                    "method": "Scene-adaptive motion compensation.",
                    "scenario": "airborne SAR / high-resolution / large-squint",
                    "contributions": [
                        "Models azimuth-variant effects.",
                        "Improves image focus under large squint.",
                    ],
                    "speed_related_issue": None,
                    "squint_related_issue": "Addresses azimuth-variant effects under large squint angles.",
                    "datasets_or_simulation": ["simulated flight path"],
                    "metrics": ["PSLR", "ISLR", "resolution"],
                    "limitations": ["Sensitive to severe motion error."],
                },
                entities_json={"methods": ["motion-compensation", "omega-k"]},
                analysis_model="openai",
                embedding_model="openai",
                prompt_version="v1",
            ),
            PaperAnalysis(
                paper_id=papers[1].id,
                summary_json={
                    "problem": "Maintain high-resolution SAR imaging for high-speed platforms.",
                    "method": "Motion compensation with focused imaging refinement.",
                    "scenario": "airborne SAR / high-resolution / high-speed",
                    "contributions": [
                        "Handles platform dynamics during high-speed acquisition.",
                        "Improves focus consistency under motion variation.",
                    ],
                    "speed_related_issue": "Handles platform dynamics during high-speed acquisition.",
                    "squint_related_issue": None,
                    "datasets_or_simulation": ["simulated flight path"],
                    "metrics": ["PSLR", "ISLR", "resolution"],
                    "limitations": ["Needs trajectory estimates."],
                },
                entities_json={"methods": ["motion-compensation", "autofocus"]},
                analysis_model="openai",
                embedding_model="openai",
                prompt_version="v1",
            ),
        ]
    )

    db.add_all(
        [
            ProcessingTask(paper_id=papers[0].id, task_name="generate_summary", state="completed", provider="openai", payload={}),
            ProcessingTask(paper_id=papers[1].id, task_name="generate_summary", state="queued", provider="openai", payload={}),
        ]
    )
    db.commit()
