import sqlalchemy

from .base import Base


class Workflow(Base):
    """Workflow entity for persistence"""

    __tablename__ = 'workflows'

    uuid = sqlalchemy.Column(sqlalchemy.String(255), primary_key=True, unique=True)
    name = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    bot_id = sqlalchemy.Column(sqlalchemy.String(255), nullable=True)  # Optional bot association
    trigger_type = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    trigger_config = sqlalchemy.Column(sqlalchemy.JSON, nullable=False, default={})
    nodes = sqlalchemy.Column(sqlalchemy.JSON, nullable=False, default=[])
    edges = sqlalchemy.Column(sqlalchemy.JSON, nullable=False, default=[])
    status = sqlalchemy.Column(sqlalchemy.String(255), nullable=False, default='DRAFT')
    version = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=1)
    workflow_metadata = sqlalchemy.Column(sqlalchemy.JSON, nullable=False, default={})
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, server_default=sqlalchemy.func.now())
    updated_at = sqlalchemy.Column(
        sqlalchemy.DateTime,
        nullable=False,
        server_default=sqlalchemy.func.now(),
        onupdate=sqlalchemy.func.now(),
    )


class WorkflowExecutionRecord(Base):
    """Workflow execution record"""

    __tablename__ = 'workflow_execution_records'

    uuid = sqlalchemy.Column(sqlalchemy.String(255), primary_key=True, unique=True)
    workflow_uuid = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    trigger_data = sqlalchemy.Column(sqlalchemy.JSON, nullable=False, default={})
    status = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    started_at = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, server_default=sqlalchemy.func.now())
    finished_at = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    execution_path = sqlalchemy.Column(sqlalchemy.JSON, nullable=False, default=[])
    node_outputs = sqlalchemy.Column(sqlalchemy.JSON, nullable=False, default={})
    error = sqlalchemy.Column(sqlalchemy.TEXT, nullable=True)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, server_default=sqlalchemy.func.now())