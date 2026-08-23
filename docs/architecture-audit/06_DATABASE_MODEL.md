# 06 — Database Model

Evidence: `revenue_os/models/*`, `revenue_os/database.py`, `alembic.ini`, `migrations/`, startup code in `runner_api.py` / `revenue_os/main.py`.

---

## ORM

- SQLAlchemy 2.x declarative style (`DeclarativeBase` in `revenue_os/models/base.py`).
- Session factory: `revenue_os/database.py` → `engine`, `SessionLocal`, `get_db()`.
- Engine options: `pool_pre_ping=True`, `pool_size=10`, `max_overflow=20`.

---

## Alembic

| Item | Evidence |
|------|----------|
| Config | `alembic.ini` → `script_location = %(here)s/migrations` |
| Env | `migrations/env.py` |
| Versions present | `migrations/versions/e8278e1169e6_full_schema.py` |
| Revision ID | `e8278e1169e6` |
| `down_revision` | `None` (root) |
| `upgrade()` / `downgrade()` body | `pass` only (no DDL operations in file) |

---

## Database initialization

| Path | Behavior evidenced |
|------|--------------------|
| `revenue_os/main.py` startup | `Base.metadata.create_all(bind=engine)` |
| `runner_api.py` startup | Schema create + `_migrate_missing_columns()` additive `ALTER TABLE` patches (Postgres vs SQLite branches) |
| Demo | `scripts/init_demo_db.py`, `scripts/clear_demo_data.py` |

---

## Models (SQLAlchemy `Base` subclasses)

Count of `class X(Base)` under `revenue_os/models`: **44** (including records; excluding enums).

### Contact / company (`contact.py`)
- `Company` — table `companies`; `domain` unique+index; relationships to contacts, deals, projects
- `Contact` — table `contacts`; FK `companies.id`; relationships to company, deals, activities

### Deals (`deal.py`)
- `Pipeline` — `pipelines`
- `Deal` — `deals`; FKs to pipelines, companies, contacts

### Activities / outreach (`activity.py`)
- `Activity` — FKs contacts, deals
- `EmailActivity`, `MeetingActivity`
- `OutreachSequence`, `SequenceStep` (FK to sequences)

### Content / KB (`content.py`)
- `KnowledgeBase`, `KnowledgeBaseArticle`
- `ContentLibrary`, `SocialPost`
- `Article` — `content_id` unique+index

### Projects / billing (`project.py`)
- `Client`, `TeamMember`, `Project`, `Milestone`, `Deliverable`, `BillingRecord` (`invoice_number` unique)

### Recruitment (`recruitment.py`)
- `JobDescription`, `Candidate`, `Interview`, `Placement`

### Automation (`automation.py`)
- `Trigger`, `Action`, `Workflow`, `WorkflowStep`, `WorkflowExecution`

### Automation state (`automation_state.py`)
- `AgentActionLog`, `HeartbeatRun`, `AnalyticsMetricRecord`, `AnalyticsDataPointRecord`, `WorkflowDefinitionRecord`

### Agents (`agents.py`)
- `AgentRegistryRecord` (PK `name`), `AgentMessageRecord`

### Goals / approvals / SEO / integrations / analytics
- `Goal`, `GoalStep` (`hermes_goals`, `hermes_goal_steps`)
- `ApprovalRequest`
- `SEOKeyword`, `SEORankCheck`
- `ConnectorCredentialRecord` (PK `connector_name`)
- `MarketingSpendRecord` (`marketing_spend`)
- `User` (`users`)

Exported aggregate list: `revenue_os/models/__init__.py`.

---

## Relationships (representative)

Documented via `relationship(...)` / `ForeignKey` in model files:

- Company ↔ Contact ↔ Deal ↔ Activity
- Pipeline ↔ Deal
- KnowledgeBase ↔ KnowledgeBaseArticle
- ContentLibrary ↔ SocialPost
- Client ↔ Project ↔ Milestone/Deliverable/BillingRecord
- JobDescription ↔ Candidate ↔ Interview/Placement
- Workflow ↔ WorkflowStep / WorkflowExecution
- SEOKeyword ↔ SEORankCheck

---

## Indexes / constraints

| Kind | Evidence |
|------|----------|
| Primary keys | UUID/`String`/`Integer` PKs on models |
| Unique columns | e.g. `Company.domain`, `Article.content_id`, `BillingRecord.invoice_number` |
| Column indexes | `index=True` on selected columns (e.g. `domain`, `content_id`) |
| Explicit `Index(...)` constructs | **Repository evidence not found** under `revenue_os/models` |
| Explicit `UniqueConstraint(...)` | **Repository evidence not found** under `revenue_os/models` |

---

## Migration history

| Revision | Date string in file | Operations |
|----------|---------------------|------------|
| `e8278e1169e6` | 2026-06-11 01:57:36.490868 | empty `pass` upgrade/downgrade |

No additional revision files found under `migrations/versions/`.
