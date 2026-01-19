"""Add user notification prefs and consistency fields

Revision ID: cf4e9ce6057e
Revises: 
Create Date: 2025-12-21 00:29:58.998530

"""
fromalembicimportop
importsqlalchemyassa



revision='cf4e9ce6057e'
down_revision=None
branch_labels=None
depends_on=None


defupgrade():

    withop.batch_alter_table('user',schema=None)asbatch_op:
        batch_op.add_column(sa.Column('workout_reminder',sa.Boolean(),nullable=True))
batch_op.add_column(sa.Column('meal_reminder',sa.Boolean(),nullable=True))
batch_op.add_column(sa.Column('progress_summary_frequency',sa.String(length=20),nullable=True))




defdowngrade():

    withop.batch_alter_table('user',schema=None)asbatch_op:
        batch_op.drop_column('progress_summary_frequency')
batch_op.drop_column('meal_reminder')
batch_op.drop_column('workout_reminder')


