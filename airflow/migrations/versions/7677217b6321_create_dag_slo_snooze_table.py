#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Create dag_slo_snooze table.

Revision ID: 7677217b6321
Revises: 9635ae0956e7
Create Date: 2018-12-12 16:28:45.003946

"""

# revision identifiers, used by Alembic.
revision = '7677217b6321'
down_revision = '9635ae0956e7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSTZRANGE


def upgrade():
    op.create_table(
        "dag_slo_snooze",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("dag_id", sa.String(length=250), nullable=False),
        sa.Column("snooze_range", TSTZRANGE, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Text(), nullable=False),
    )


def downgrade():
    op.drop_table("dag_slo_snooze")
