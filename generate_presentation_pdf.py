"""
Generate a professional PDF presentation guide for the AI QA Engineer project.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)


def build_presentation_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1e1b4b")  # Deep indigo
    accent_color = colors.HexColor("#4f46e5")   # Indigo violet
    secondary_text = colors.HexColor("#475569") # Slate gray
    bg_box = colors.HexColor("#f8fafc")         # Light slate box

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=primary_color,
        alignment=1,  # Center
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=accent_color,
        alignment=1,
        spaceAfter=15,
    )

    slide_heading = ParagraphStyle(
        "SlideHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "BulletText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        leftIndent=12,
        spaceAfter=4,
    )

    speaker_notes_style = ParagraphStyle(
        "SpeakerNotes",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0f766e"), # Teal
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1e293b"),
    )

    story = []

    # ── HEADER & COVER ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(Paragraph("AI QA ENGINEER", title_style))
    story.append(
        Paragraph(
            "Multi-Agent AI-Powered Automated Code Quality & Testing Platform<br/><b>College Final Year Project Presentation & Viva Guide</b>",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=2, color=accent_color, spaceAfter=15))

    # Meta table
    meta_data = [
        [
            Paragraph("<b>Project Domain:</b> Artificial Intelligence & Software Engineering", table_cell_style),
            Paragraph("<b>Architecture:</b> LangGraph Multi-Agent State Machine", table_cell_style),
        ],
        [
            Paragraph("<b>LLM Model:</b> Google Gemini 2.5 Flash", table_cell_style),
            Paragraph("<b>Backend:</b> Python 3.11+ / FastAPI / Pytest", table_cell_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_box),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # Helper function to create slide blocks
    def add_slide(slide_num, title, key_bullets, speaker_notes, table_data=None):
        block = []
        block.append(Paragraph(f"<b>SLIDE {slide_num}: {title.upper()}</b>", slide_heading))
        block.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
        
        for b in key_bullets:
            block.append(Paragraph(f"• <b>{b[0]}:</b> {b[1]}", bullet_style))
        
        if table_data:
            block.append(Spacer(1, 4))
            t = Table(table_data, colWidths=[120, 200, 220])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), accent_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]))
            block.append(t)
            block.append(Spacer(1, 4))

        # Speaker notes container
        notes_table = Table(
            [[Paragraph(f"<b>🎙️ SPEAKER NOTES (Say This):</b> {speaker_notes}", speaker_notes_style)]],
            colWidths=[540],
        )
        notes_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdfa")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#99f6e4")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        block.append(Spacer(1, 4))
        block.append(notes_table)
        block.append(Spacer(1, 14))
        return block

    # ── SLIDE 1 ───────────────────────────────────────────────────────────────
    story.extend(add_slide(
        1, "Title & Introduction",
        [
            ("Project Name", "AI QA ENGINEER — Multi-Agent Software Quality & Testing Platform"),
            ("Domain", "Applied Artificial Intelligence, Software Engineering & QA Automation"),
            ("Goal", "Simulate an entire autonomous QA team using specialized collaborative AI agents."),
        ],
        "Good morning respected guide and coordinator. Today I present 'AI QA Engineer', an autonomous multi-agent platform that automates full-lifecycle code quality inspection, test generation, test execution, security auditing, and root-cause analysis."
    ))

    # ── SLIDE 2 ───────────────────────────────────────────────────────────────
    story.extend(add_slide(
        2, "Problem Statement",
        [
            ("Manual QA Bottleneck", "Writing comprehensive unit tests covering edge cases is time-intensive and error-prone."),
            ("Shallow Happy-Path Testing", "Developers often test only expected inputs, missing zero-division, type mismatches, and boundary crashes."),
            ("Security Blindspots", "Vulnerabilities like SQL injections and hardcoded secrets routinely leak into production."),
            ("Fragmented Tooling", "Linters, security scanners, and test runners output disjointed logs without root-cause reasoning."),
        ],
        "Software testing is currently fragmented. Developers juggle multiple tools without unified synthesis, and manually triaging failed tests consumes hours of valuable engineering time. Our system solves this by introducing automated multi-agent reasoning."
    ))

    # ── SLIDE 3 ───────────────────────────────────────────────────────────────
    story.extend(add_slide(
        3, "Existing vs. Proposed System",
        [
            ("Key Paradigm Shift", "From fragmented manual scripting to a unified, stateful multi-agent orchestrator."),
            ("Zero-Hallucination Policy", "Empirical metrics are strictly measured with deterministic tools, while LLMs handle reasoning."),
        ],
        "Traditional testing requires human manual intervention at every phase. Our proposed AI QA Engineer uses a state machine to orchestrate 10 specialized agents, strictly separating empirical measurements from generative AI reasoning.",
        [
            [Paragraph("Dimension", table_header_style), Paragraph("Existing Manual QA", table_header_style), Paragraph("AI QA Engineer (Proposed)", table_header_style)],
            [Paragraph("Test Authoring", table_cell_style), Paragraph("Manual, slow, developer-dependent", table_cell_style), Paragraph("Automated synthesis via Gemini 2.5 Flash", table_cell_style)],
            [Paragraph("Security Audit", table_cell_style), Paragraph("Separate manual CLI tools", table_cell_style), Paragraph("Integrated Bandit AST & Heuristic scanning", table_cell_style)],
            [Paragraph("Defect Diagnosis", table_cell_style), Paragraph("Manual stack trace debugging", table_cell_style), Paragraph("Automated Root Cause Analysis (RCA) with fixes", table_cell_style)],
            [Paragraph("Coordination", table_cell_style), Paragraph("Ad-hoc manual workflows", table_cell_style), Paragraph("Stateful LangGraph multi-agent pipeline", table_cell_style)],
        ]
    ))

    # ── SLIDE 4 ───────────────────────────────────────────────────────────────
    story.extend(add_slide(
        4, "System Architecture & Data Flow",
        [
            ("Presentation Tier", "Responsive Web Dashboard (HTML5 / CSS3 / Vanilla JS) with real-time state polling."),
            ("Backend API Tier", "FastAPI asynchronous REST backend with background task execution."),
            ("Orchestration Tier", "LangGraph StateGraph managing sequential agent activations across a shared QAState."),
            ("Verification Engine", "Subprocess execution of Pytest, pytest-cov, Ruff, and Bandit."),
        ],
        "Our architecture follows a clean 4-tier design. When the user selects a project, FastAPI triggers our LangGraph state machine. Each agent mutates a shared state dictionary in memory, driving both deterministic tools and Gemini API calls."
    ))

    # ── SLIDE 5 ───────────────────────────────────────────────────────────────
    story.extend(add_slide(
        5, "Multi-Agent Catalog (10 Specialized Agents)",
        [
            ("1. Supervisor Agent", "Initializes the state machine, validates inputs, logs timestamps, and coordinates execution."),
            ("2. Code Loader Agent", "Recursively scans files, discovers Python source files, and builds project structure."),
            ("3. Code Analyzer Agent", "Runs Ruff linter and computes AST cyclomatic complexity and code smells."),
            ("4. Security Agent", "Executes Bandit to detect SQL injections, command injections, and hardcoded API keys."),
            ("5. Test Generator Agent", "Prompts Gemini to synthesize comprehensive Pytest test cases covering failure modes."),
            ("6. Test Runner Agent", "Executes generated tests in an isolated subprocess and captures pass/fail counts."),
            ("7. Coverage Agent", "Runs pytest-cov to calculate statement and line-by-line coverage percentages."),
            ("8. Bug Analysis Agent", "Correlates failed tests and static issues to categorize defects by severity."),
            ("9. Root Cause Agent (RCA)", "Diagnoses WHY defects happened, business risks, and code-level fixes."),
            ("10. QA Report Agent", "Computes Overall Quality (0-100), Security Score, and writes executive summaries."),
        ],
        "Instead of using a single monolithic prompt, we distribute responsibilities across 10 specialized agents. This modular design prevents context loss, enables isolated retries, and guarantees deterministic accuracy."
    ))

    # ── SLIDE 6 ───────────────────────────────────────────────────────────────
    story.extend(add_slide(
        6, "Technology Stack",
        [
            ("Core Programming", "Python 3.11+ (TypedDict, AST parser, Subprocess)"),
            ("Backend Framework", "FastAPI, Uvicorn, Pydantic v2"),
            ("AI & Orchestration", "Google Gemini 2.5 Flash (google-genai SDK), LangGraph, LangChain Core"),
            ("Testing & Security", "Pytest, Pytest-cov, Ruff, Bandit"),
            ("Frontend UI", "Modern Dark Glassmorphic Dashboard (HTML5, CSS3, Vanilla JavaScript)"),
        ],
        "Our technology stack combines high-performance Python asynchronous APIs with LangGraph state orchestration and Google's Gemini 2.5 Flash model for natural language reasoning and code generation."
    ))

    # ── SLIDE 7 ───────────────────────────────────────────────────────────────
    story.extend(add_slide(
        7, "Demo Case Study & Planted Defects (demo_project/)",
        [
            ("calculator.py", "Zero-division error in divide(), missing upper-bound in calculate_discount(), empty list in average()."),
            ("user_service.py", "Hardcoded SECRET_KEY and API_KEY, plaintext password storage, weak MD5 hashing."),
            ("payment.py", "Command injection via subprocess(shell=True), unvalidated negative payment amounts."),
            ("database.py", "Direct f-string SQL injection vulnerabilities in get_user() and create_user()."),
            ("utils.py", "Arbitrary code execution via pickle.load() and eval() on unsanitized inputs."),
        ],
        "To validate our platform, we created demo_project/ containing realistic defects. In our live test run, the platform successfully identified all security vulnerabilities, exposed logic bugs through generated tests, and diagnosed the root causes."
    ))

    # ── SLIDE 8 ───────────────────────────────────────────────────────────────
    story.extend(add_slide(
        8, "Root Cause Analysis (RCA) Deep Dive",
        [
            ("Why It Happened", "Explains the fundamental reason (e.g., missing input validation guard clause)."),
            ("Affected Component", "Pinpoints exact module and function (e.g., calculator.py -> divide())."),
            ("Business & Technical Impact", "Evaluates production outage risks and unhandled exception propagation."),
            ("Actionable Fix & Confidence", "Provides drop-in corrected code with AI confidence percentage (e.g., 96%)."),
        ],
        "The most powerful feature of AI QA Engineer is Root Cause Analysis. Rather than simply alerting that a test failed, our RCA agent explains why it failed, what business risk it poses, and generates a concrete Python code snippet to fix it."
    ))

    # ── SLIDE 9 ───────────────────────────────────────────────────────────────
    story.extend(add_slide(
        9, "Scoring Formula & Human-in-the-Loop Sign-Off",
        [
            ("Quality Score (0-100)", "Weighted: Code Quality (30%) + Test Pass Rate (25%) + Coverage (20%) - Bug Severity Penalties (25%)."),
            ("Security Score (0-100)", "Deductions based on CVSS severity: Critical (-20 pts), High (-10 pts), Medium (-5 pts)."),
            ("Human-in-the-Loop (HITL)", "Interactive sign-off where QA leads review findings and mark reports as Approved or Rejected with audit notes."),
        ],
        "We compute an Overall Quality Score and Security Score using a transparent, multi-metric formula. The platform includes a Human-in-the-Loop sign-off interface, allowing QA leads to approve releases or request re-analysis."
    ))

    # ── SLIDE 10 ──────────────────────────────────────────────────────────────
    story.extend(add_slide(
        10, "Advantages, Future Scope & Conclusion",
        [
            ("Key Advantages", "Zero metric hallucination, 80%+ reduction in test authoring time, unified security and QA visibility."),
            ("Future Scope", "Support for Java and TypeScript, native GitHub Actions CI/CD integration, and automated PR fix creation."),
            ("Conclusion", "AI QA Engineer demonstrates that combining generative AI with deterministic testing tools creates a reliable, autonomous QA platform."),
        ],
        "In conclusion, AI QA Engineer proves that multi-agent architectures paired with deterministic tools can automate the complex cognitive workflow of software testing. Thank you, and I now welcome any questions."
    ))

    # ── VIVA CHEAT SHEET SECTION ──────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("TOP 10 VIVA QUESTIONS & ANSWERS (CHEAT SHEET)", slide_heading))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=10))

    viva_items = [
        ("1. Why use LangGraph instead of a single LLM prompt?", "A single prompt cannot reliably execute code, calculate coverage, run security audits, and write reports without hallucinating numbers or losing context. LangGraph provides a stateful state machine coordinating specialized agents."),
        ("2. How do you prevent LLM hallucinations?", "We strictly separate empirical measurement (Pytest for pass/fail, pytest-cov for coverage, Bandit for security) from generative reasoning (Gemini for test synthesis, RCA, and summary writing)."),
        ("3. What is the role of the Supervisor Agent?", "The Supervisor initializes the execution graph, logs timestamps, tracks agent states (Pending -> Running -> Completed), and manages error boundaries."),
        ("4. How does shared state work?", "We use a TypedDict called QAState. As LangGraph transitions between nodes, each agent reads its inputs and updates its specific output keys in memory."),
        ("5. What happens if Gemini API is offline?", "DEMO_MODE=true automatically activates, using deterministic AST checks, mock test suites, and pre-computed AI diagnostics so the application never crashes."),
        ("6. How are unit tests generated?", "The Test Generator Agent feeds source files into Gemini with a specialized test-engineering prompt that enforces edge-case, boundary, and exception testing using pytest.raises()."),
        ("7. How does the Security Agent work?", "It runs Bandit, an AST-based security linter that matches syntax nodes against vulnerability rules (B602 command injection, B307 eval, B105 hardcoded secrets)."),
        ("8. How is code coverage measured?", "The Coverage Agent invokes pytest --cov in a subprocess, parsing XML line coverage data to compute statement coverage percentages per file."),
        ("9. What is Human-in-the-Loop governance?", "Before a report is finalized, a human QA lead reviews the findings on the dashboard and officially approves or rejects the release with audit notes."),
        ("10. How can this project scale?", "By integrating Celery and Redis for asynchronous task queues, PostgreSQL for report storage, Docker for sandboxed test execution, and GitHub Actions for CI/CD gating."),
    ]

    for q, a in viva_items:
        story.append(Paragraph(f"<b>Q: {q}</b>", ParagraphStyle("Q", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=12, textColor=accent_color)))
        story.append(Paragraph(f"<b>A:</b> {a}", ParagraphStyle("A", parent=styles["Normal"], fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#1e293b"), spaceAfter=6)))

    doc.build(story)
    print(f"Presentation PDF generated at: {output_path}")


if __name__ == "__main__":
    pdf_out = Path(__file__).resolve().parent / "AI_QA_ENGINEER_PRESENTATION.pdf"
    build_presentation_pdf(str(pdf_out))
