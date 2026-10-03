"""Keep PostgreSQL extension-owned tables out of application autogeneration."""
from sqlalchemy import text


def extension_table_filter(connection):
    if connection.dialect.name != 'postgresql':
        return lambda name, type_, parents: True
    rows = connection.execute(text("""
        SELECT n.nspname, c.relname, pg_table_is_visible(c.oid)
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_depend d ON d.objid = c.oid AND d.classid = 'pg_class'::regclass
        JOIN pg_extension e ON e.oid = d.refobjid AND d.refclassid = 'pg_extension'::regclass
        WHERE d.deptype = 'e' AND c.relkind IN ('r', 'p')
    """))
    excluded = set()
    for schema, name, visible in rows:
        excluded.add((schema, name))
        if visible:
            excluded.add((None, name))

    def include_name(name, type_, parents):
        # Only extension membership is excluded. Unknown application tables and
        # missing/changed application columns must still be reported as drift.
        return type_ != 'table' or (parents.get('schema_name'), name) not in excluded

    return include_name
