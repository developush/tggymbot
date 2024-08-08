"""Peewee migrations -- 002_add_programs.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['model_name']            # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.python(func, *args, **kwargs)        # Run python code
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.drop_index(model, *col_names)
    > migrator.add_not_null(model, *field_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)

"""

import peewee as pw

try:
    import playhouse.postgres_ext as pw_pext
except ImportError:
    pass

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""

    @migrator.create_model
    class ProgramGroup(pw.Model):
        id = pw.AutoField()
        name = pw_pext.BinaryJSONField(constraints=[SQL("DEFAULT '{}'")], index=True)
        order = pw.IntegerField(default=0)
        days_between_trainings = pw.IntegerField(default=1)
        created = pw.DateTimeField(index=True)

        class Meta:
            db_table = 'program_groups'

    @migrator.create_model
    class ProgramLevel(pw.Model):
        id = pw.AutoField()
        name = pw_pext.BinaryJSONField(constraints=[SQL("DEFAULT '{}'")], index=True)
        order = pw.IntegerField(default=0)
        created = pw.DateTimeField(index=True)

        class Meta:
            table_name = "program_levels"

    @migrator.create_model
    class Program(pw.Model):
        id = pw.AutoField()
        group = pw.ForeignKeyField(backref='program_set', column_name='group_id',
                                   field='id', model=migrator.orm['program_groups'])
        level = pw.ForeignKeyField(backref='program_set', column_name='level_id',
                                   field='id', model=migrator.orm['program_levels'])
        description = pw_pext.BinaryJSONField(constraints=[SQL("DEFAULT '{}'")])
        exercises = pw_pext.BinaryJSONField(constraints=[SQL("DEFAULT '[]'")])
        created = pw.DateTimeField(index=True)

        class Meta:
            db_table = 'programs'

    migrator.add_fields(
        'users',
        program=pw.ForeignKeyField(backref='users_set', column_name='program_id',
                                   field='id', model=migrator.orm['programs'])
    )


def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""

    migrator.remove_model('program_groups')

    migrator.remove_model('program_levels')

    migrator.remove_model('programs')

    migrator.remove_fields('users', 'program')
