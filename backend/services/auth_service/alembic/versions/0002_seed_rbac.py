"""seed RBAC roles and permissions

Revision ID: 0002_seed_rbac
Revises: 0001_init_auth
Create Date: 2026-04-26
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_seed_rbac"
down_revision: Union[str, None] = "0001_init_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSIONS = [
    ("production", "read"), ("production", "write"),
    ("production", "delete"), ("production", "export"),
    ("maintenance", "read"), ("maintenance", "write"), ("maintenance", "delete"),
    ("ml", "read"), ("ml", "predict"), ("ml", "train"), ("ml", "delete"),
    ("reports", "read"), ("reports", "export"),
    ("users", "read"), ("users", "write"), ("users", "delete"),
    ("roles", "read"), ("roles", "write"),
    ("audit", "read"),
]

ROLE_PERMS = {
    "admin": [("*", "*")],
    "engineer": [
        ("production", "read"), ("production", "write"),
        ("maintenance", "read"), ("maintenance", "write"),
        ("ml", "read"), ("ml", "predict"), ("ml", "train"),
        ("reports", "read"), ("reports", "export"),
    ],
    "analyst": [
        ("production", "read"), ("maintenance", "read"),
        ("ml", "read"), ("ml", "predict"),
        ("reports", "read"), ("reports", "export"),
    ],
    "viewer": [
        ("production", "read"), ("maintenance", "read"), ("reports", "read"),
    ],
}


def upgrade() -> None:
    op.execute("INSERT INTO auth.permissions (resource, action) VALUES ('*', '*') ON CONFLICT DO NOTHING")
    for resource, action in PERMISSIONS:
        op.execute(
            f"INSERT INTO auth.permissions (resource, action) "
            f"VALUES ('{resource}', '{action}') ON CONFLICT DO NOTHING"
        )

    for role_name, perms in ROLE_PERMS.items():
        op.execute(
            f"INSERT INTO auth.roles (name, description) "
            f"VALUES ('{role_name}', '{role_name} role') ON CONFLICT DO NOTHING"
        )
        for resource, action in perms:
            op.execute(f"""
                INSERT INTO auth.role_permissions (role_id, permission_id)
                SELECT r.id, p.id
                FROM auth.roles r, auth.permissions p
                WHERE r.name = '{role_name}'
                  AND p.resource = '{resource}' AND p.action = '{action}'
                ON CONFLICT DO NOTHING
            """)


def downgrade() -> None:
    op.execute("DELETE FROM auth.role_permissions")
    op.execute("DELETE FROM auth.roles WHERE name IN ('admin','engineer','analyst','viewer')")
    op.execute("DELETE FROM auth.permissions")
