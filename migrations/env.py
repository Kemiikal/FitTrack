importlogging
fromlogging.configimportfileConfig

fromflaskimportcurrent_app

fromalembicimportcontext



config=context.config



fileConfig(config.config_file_name)
logger=logging.getLogger('alembic.env')


defget_engine():
    try:

        returncurrent_app.extensions['migrate'].db.get_engine()
except(TypeError,AttributeError):

        returncurrent_app.extensions['migrate'].db.engine


defget_engine_url():
    try:
        returnget_engine().url.render_as_string(hide_password=False).replace(
'%','%%')
exceptAttributeError:
        returnstr(get_engine().url).replace('%','%%')






config.set_main_option('sqlalchemy.url',get_engine_url())
target_db=current_app.extensions['migrate'].db







defget_metadata():
    ifhasattr(target_db,'metadatas'):
        returntarget_db.metadatas[None]
returntarget_db.metadata


defrun_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
url=config.get_main_option("sqlalchemy.url")
context.configure(
url=url,target_metadata=get_metadata(),literal_binds=True
)

withcontext.begin_transaction():
        context.run_migrations()


defrun_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """




defprocess_revision_directives(context,revision,directives):
        ifgetattr(config.cmd_opts,'autogenerate',False):
            script=directives[0]
ifscript.upgrade_ops.is_empty():
                directives[:]=[]
logger.info('No changes in schema detected.')

conf_args=current_app.extensions['migrate'].configure_args
ifconf_args.get("process_revision_directives")isNone:
        conf_args["process_revision_directives"]=process_revision_directives

connectable=get_engine()

withconnectable.connect()asconnection:
        context.configure(
connection=connection,
target_metadata=get_metadata(),
**conf_args
)

withcontext.begin_transaction():
            context.run_migrations()


ifcontext.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
