# AI QA ENGINEER — Viva & Oral Examination Preparation Guide 🎓

This document contains 25+ essential viva examination questions and answers tailored for the **AI QA Engineer** project presentation.

---

### Q1: What is the core problem that AI QA Engineer solves?
**Answer:** Traditional software testing is fragmented and labor-intensive. Developers spend excessive time manually writing boilerplate unit tests, configuring linters and security scanners, executing test runs, and deciphering error stack traces. AI QA Engineer unifies these disjointed activities into an autonomous, multi-agent pipeline that analyzes code, discovers bugs, generates and executes tests, determines root causes, and generates a consolidated release report.

---

### Q2: What is a Multi-Agent System (MAS), and why use it here?
**Answer:** A Multi-Agent System is an architectural pattern where a complex objective is broken down into specialized autonomous entities (agents), each having a distinct role, tools, and cognitive scope. We use it instead of a single LLM because a single prompt cannot reliably parse ASTs, execute bash subprocesses, run Pytest, calculate line coverage, and write reports without losing context, hallucinating data, or running into token limits.

---

### Q3: Why did you choose LangGraph for orchestration?
**Answer:** LangGraph provides a cyclic and stateful graph-based orchestration framework built on top of LangChain. Unlike standard linear chains, LangGraph uses a shared typed state (`QAState`) where each node represents an isolated agent function. It allows fine-grained state transitions, branching, error recovery, and seamless human-in-the-loop checkpointing.

---

### Q4: Why not just ask a single LLM like ChatGPT or Claude to do everything in one prompt?
**Answer:** Single-prompt architectures suffer from four major limitations:
1. **Hallucination of Metrics**: An LLM cannot execute code; it will fabricate test pass/fail counts and coverage percentages.
2. **Context Degradation**: Uploading an entire multi-file codebase into a single prompt degrades attention and leads to missed edge cases.
3. **Lack of Tool Coupling**: Agents need deterministic execution tools (Bandit, Pytest, Ruff) to obtain empirical ground truth.
4. **No Modular Retries**: In a multi-agent system, if test generation fails, only the Test Generator agent retries without restarting the whole analysis.

---

### Q5: What is the role of the Supervisor Agent?
**Answer:** The Supervisor Agent initializes the global execution graph, validates inputs, logs timestamps, tracks the lifecycle of each agent node (Pending → Running → Completed/Failed), and ensures that all downstream agents receive the required state keys before finalizing the QA report.

---

### Q6: How does shared state work in your architecture?
**Answer:** We defined `QAState` using Python's `TypedDict`. As the graph transitions from node to node, each agent receives the current state object, extracts the variables it needs (e.g., `source_files`), performs its tasks, updates its specific output keys (e.g., `security_results`), and returns the mutated state to LangGraph.

---

### Q7: Why did you choose FastAPI for the backend?
**Answer:** FastAPI is a high-performance, asynchronous web framework built on Starlette and Pydantic. It provides:
- Native asynchronous request handling (`async`/`await`), allowing non-blocking background analysis tasks.
- Automatic data validation and serialization using Pydantic models.
- Auto-generated OpenAPI (Swagger) documentation.
- High throughput suitable for handling concurrent QA jobs.

---

### Q8: How do you prevent LLM hallucinations in your quality metrics?
**Answer:** We strictly separate **empirical measurement** from **generative reasoning**:
- **Test execution & pass rate** are measured deterministically using `pytest`.
- **Code coverage** is calculated by `pytest-cov` from line execution traces.
- **Security vulnerabilities** are detected using AST rules via `Bandit`.
- **Code complexity** is computed by traversing Python's `ast` module.
The LLM (Gemini) is only utilized for tasks that require natural language understanding: synthesizing test logic, explaining root causes, assessing business impact, and writing the executive summary.

---

### Q9: How are the Pytest test cases generated?
**Answer:** The Test Generator Agent extracts non-test Python source files, feeds their structure and docstrings into Gemini 2.5 Flash using a specialized test-engineering prompt, extracts clean Python code blocks, and writes them to a temporary file (`test_ai_generated.py`). The prompt specifically instructs the model to test normal inputs, edge cases (zero values, negative numbers, empty arrays), and expected exceptions using `pytest.raises()`.

---

### Q10: How does the Test Runner Agent execute tests safely?
**Answer:** The Test Runner invokes `pytest` as an isolated subprocess using Python's `subprocess.run()`, setting a strict execution timeout (120 seconds) and passing `--rootdir` and `--tb=short` arguments. It captures standard output, standard error, and exit codes without risking crashing the FastAPI server process.

---

### Q11: How is code coverage calculated?
**Answer:** The Coverage Agent runs Pytest with the `--cov` and `--cov-report=xml` flags. It parses the generated XML coverage report or standard output to extract line-by-line hit counts, total statement counts, and calculates the exact percentage of statements executed across each module.

---

### Q12: How does the Security Agent detect vulnerabilities?
**Answer:** The Security Agent runs `Bandit`, a security linter designed to parse the Python Abstract Syntax Tree (AST) and match nodes against known security risk patterns (such as `B602` for `shell=True` subprocesses, `B307` for `eval()`, and `B105` for hardcoded secrets). If Bandit is unavailable, a heuristic pattern scanner provides resilient fallback scanning.

---

### Q13: What is Root Cause Analysis (RCA) in this project?
**Answer:** When a test fails or a critical vulnerability is flagged, the Root Cause Analysis Agent isolates the failing component, looks at the source code snippet, and prompts Gemini to diagnose:
1. The fundamental underlying reason why the defect exists.
2. The exact affected function and file.
3. The business risk (e.g., service outage, financial loss).
4. The technical impact (e.g., unhandled exception propagation).
5. A concrete code-level fix with estimated complexity and confidence percentage.

---

### Q14: What is "Human-in-the-Loop" (HITL) and how is it implemented?
**Answer:** Human-in-the-Loop ensures that automated AI decisions are supervised by human experts before taking critical actions. In our system, once the agents generate the final report, the status remains `Pending Approval`. A human QA lead can review all findings on the dashboard and click `Approve Report` or `Request Re-Analysis`, adding audit notes via `/api/approve/{job_id}`.

---

### Q15: What happens if Gemini API access fails or is offline?
**Answer:** We engineered a resilient **Fallback / Demo Mode** (`DEMO_MODE=true`). If the `GEMINI_API_KEY` is missing or the network request times out, the `GeminiService` automatically switches to deterministic, context-aware mock responses for test generation, bug diagnosis, and RCA. The backend logs the switch, and the UI displays a `Demo / Fallback Mode Active` badge, ensuring the platform never crashes during an evaluation.

---

### Q16: How is the Overall Quality Score computed?
**Answer:** The QA Report Agent uses a weighted scoring formula (0–100):
- **Base Score**: 100 points
- **Code Quality Contribution (30%)**: Scaled from Ruff and AST complexity findings.
- **Test Pass Rate (25%)**: Penalized proportionally for failed tests.
- **Code Coverage (20%)**: Penalized if total line coverage falls below the 80% industry benchmark.
- **Bug Deductions (25%)**: -8 points per Critical bug, -4 points per Major bug, and -1 point per Minor bug.

---

### Q17: What are the primary planted bugs in your `demo_project/`?
**Answer:**
1. `calculator.py`: ZeroDivisionError in `divide()`, missing upper-bound validation in `calculate_discount()`, empty list crash in `average()`.
2. `user_service.py`: Hardcoded `SECRET_KEY`, plaintext password storage, MD5 hashing.
3. `payment.py`: Command injection via `subprocess.run(..., shell=True)` with user input, unvalidated negative payment amounts.
4. `database.py`: SQL injection via raw f-string formatting in `get_user()` and `create_user()`.
5. `utils.py`: Insecure deserialization via `pickle.load()` and code injection via `eval()`.

---

### Q18: How would you scale this system to handle large enterprise repositories?
**Answer:**
1. **Asynchronous Task Queue**: Integrate **Celery** with **Redis** or **RabbitMQ** to distribute analysis jobs across multiple worker nodes.
2. **Persistent Database**: Transition from the in-memory job store to **PostgreSQL** using SQLAlchemy or Tortoise-ORM for historical reporting and audit logs.
3. **Incremental Analysis**: Analyze only changed files using Git diffs rather than re-scanning entire repositories on every commit.
4. **Sandboxed Test Execution**: Run generated tests inside isolated **Docker** containers to prevent malicious code execution during testing.

---

### Q19: Why did you build the frontend using Vanilla JS/HTML/CSS instead of React/Next.js?
**Answer:** For an MVP demonstration, Vanilla JS with modern CSS provides zero-build-step simplicity, ultra-fast initial load times, and eliminated dependency/bundling failure risks during live presentation, while maintaining a modern glassmorphic UI.

---

### Q20: How can this system support other languages like Java, C++, or JavaScript?
**Answer:** The architecture is modular:
- Replace Python AST and Ruff with language-specific AST parsers and linters (e.g., ESLint for JS, Checkstyle/SpotBugs for Java).
- Replace Pytest with standard test runners (e.g., Jest for JS, JUnit for Java).
- Update the Test Generator prompts with language-specific testing conventions. The supervisor and report aggregation graph remains unchanged.

---

### Q21: What are the security risks of executing LLM-generated code, and how can they be mitigated?
**Answer:** Executing generated tests could inadvertently run harmful commands (e.g., `os.system("rm -rf /")`). We mitigate this by:
1. Running static security checks (Bandit) on the generated test code prior to execution.
2. Setting strict process execution timeouts.
3. In production, executing tests inside ephemeral, network-isolated Docker containers with restricted capabilities.

---

### Q22: What is the difference between cyclomatic complexity and line coverage?
**Answer:** Cyclomatic complexity measures the number of linearly independent paths through a program's source code (decision points like `if`, `for`, `while`), indicating how hard a function is to test and maintain. Line coverage measures the percentage of code lines actually executed by the test suite.

---

### Q23: How does your system handle invalid or non-Python files?
**Answer:** The Code Loader Agent checks file extensions, ignores non-Python files (`.txt`, `.md`, binary assets) and common noise directories (`__pycache__`, `.venv`, `.git`), and logs graceful warning notices if individual files fail to parse.

---

### Q24: What is the significance of the `test_ai_generated.py` file?
**Answer:** It is the concrete artifact produced by the Test Generator Agent. It contains runnable Pytest code with assertions, docstrings, and test fixtures tailored to the analyzed modules, which is subsequently executed by the Test Runner Agent.

---

### Q25: What is the single biggest technical takeaway from this project?
**Answer:** The most critical takeaway is that generative AI in software engineering is most effective when paired synergistically with deterministic validation tools. LLMs excel at creative synthesis and natural language reasoning, while deterministic tools provide the uncompromised accuracy required for software verification.
