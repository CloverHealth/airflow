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

"""add max tries column to task instance

Revision ID: cc1e65623dc7
Revises: 127d2bf2dfa7
Create Date: 2017-06-19 16:53:12.851141

"""

from alembic import op
import sqlalchemy as sa

from sqlalchemy import Column, Integer, String
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision = 'cc1e65623dc7'
down_revision = '127d2bf2dfa7'
branch_labels = None
depends_on = None

Base = declarative_base()
BATCH_SIZE = 5000
ID_LEN = 250


class TaskInstance(Base):
    __tablename__ = "task_instance"

    task_id = Column(String(ID_LEN), primary_key=True)
    dag_id = Column(String(ID_LEN), primary_key=True)
    execution_date = Column(sa.DateTime, primary_key=True)
    max_tries = Column(Integer)
    try_number = Column(Integer, default=0)


def upgrade():
    op.add_column('task_instance', sa.Column('max_tries', sa.Integer, server_default="-1"))
    # Check if table task_instance exist before data migration. This check is
    # needed for database that does not create table until migration finishes.
    # Checking task_instance table exists prevent the error of querying
    # non-existing task_instance table.
    connection = op.get_bind()
    inspector = Inspector.from_engine(connection)
    tables = inspector.get_table_names()

    if TaskInstance.__tablename__ in tables:
        # Get current session
        sessionmaker = sa.orm.sessionmaker()
        session = sessionmaker(bind=connection)

        query = session.query(TaskInstance).filter(TaskInstance.max_tries == -1)
        query.update({TaskInstance.max_tries: 1})

        # Commit the current session.
        session.commit()


def downgrade():
    op.drop_column('task_instance', 'max_tries')
