"""Align the ORM with existing DraftFlow tables without replacing user data."""

from alembic import op
import sqlalchemy as sa


revision = "20261001_legacy_schema_compat"
down_revision = "20260930_authentication_init"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def _add_missing_columns(table_name: str, definitions: dict[str, sa.Column]) -> None:
    present = _columns(table_name)
    for name, definition in definitions.items():
        if name not in present:
            op.add_column(table_name, definition)


def upgrade() -> None:
    from app.database import Base
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "users" not in tables or "posts" not in tables or "comments" not in tables:
        raise RuntimeError("Expected users, posts, and comments tables before applying compatibility migration")

    _add_missing_columns(
        "users",
        {
            "role": sa.Column("role", sa.String(length=32), nullable=False, server_default="user"),
            "is_active": sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            "is_verified": sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
            "profile_visibility": sa.Column("profile_visibility", sa.String(length=20), nullable=False, server_default="public"),
            "updated_at": sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        },
    )
    _add_missing_columns(
        "posts",
        {
            "author_id": sa.Column("author_id", sa.BigInteger(), nullable=True),
            "slug": sa.Column("slug", sa.String(length=255), nullable=True),
            "status": sa.Column("status", sa.String(length=20), nullable=False, server_default="published"),
            "visibility": sa.Column("visibility", sa.String(length=20), nullable=False, server_default="public"),
            "updated_at": sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            "published_at": sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            "deleted_at": sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        },
    )
    _add_missing_columns(
        "comments",
        {
            "user_id": sa.Column("user_id", sa.BigInteger(), nullable=True),
            "updated_at": sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        },
    )
    for table_name in ("users", "posts", "comments"):
        if "updated_at" in _columns(table_name):
            op.execute(
                sa.text(
                    f"UPDATE {table_name} SET updated_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)"
                )
            )
            if op.get_bind().dialect.name == "postgresql":
                op.alter_column(
                    table_name,
                    "updated_at",
                    existing_type=sa.DateTime(timezone=True),
                    nullable=False,
                    server_default=sa.func.now(),
                )

    if op.get_bind().dialect.name == "postgresql":
        for table_name, column_name, constraint_name in (
            ("posts", "author_id", "fk_posts_author_id_users"),
            ("comments", "user_id", "fk_comments_user_id_users"),
        ):
            foreign_keys = sa.inspect(op.get_bind()).get_foreign_keys(table_name)
            if not any(column_name in fk["constrained_columns"] for fk in foreign_keys):
                op.create_foreign_key(
                    constraint_name,
                    table_name,
                    "users",
                    [column_name],
                    ["id"],
                    ondelete="SET NULL",
                )

    inspector = sa.inspect(op.get_bind())
    for table_name, index_name, column_name in (
        ("posts", "ix_posts_status", "status"),
        ("posts", "ix_posts_visibility", "visibility"),
        ("posts", "ix_posts_created_at", "created_at"),
    ):
        index_names = {index["name"] for index in inspector.get_indexes(table_name)}
        if index_name not in index_names:
            op.create_index(index_name, table_name, [column_name], unique=False)

    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    raise RuntimeError("This data-preserving compatibility migration cannot be downgraded safely")
