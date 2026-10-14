from sqlalchemy import inspect, text
from app import app, db


def repair_database():
    with app.app_context():
        # Create tables that do not exist.
        db.create_all()

        inspector = inspect(db.engine)
        model_tables = db.metadata.tables

        # Add missing columns from the current SQLAlchemy models.
        for table_name, table in model_tables.items():
            existing_tables = inspect(db.engine).get_table_names()

            if table_name not in existing_tables:
                print(f"Table not found: {table_name}")
                continue

            inspector = inspect(db.engine)
            existing_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }

            for column in table.columns:
                if column.name in existing_columns:
                    continue

                sql_type = column.type.compile(
                    dialect=db.engine.dialect
                )

                # Existing records need safe values for new NOT NULL fields.
                if column.nullable:
                    definition = sql_type

                elif column.default is not None:
                    default = column.default.arg

                    if isinstance(default, bool):
                        default_sql = "1" if default else "0"
                    elif isinstance(default, (int, float)):
                        default_sql = str(default)
                    elif isinstance(default, str):
                        default_sql = "'" + default.replace("'", "''") + "'"
                    else:
                        print(
                            f"Skipped {table_name}.{column.name}: "
                            "unsupported default."
                        )
                        continue

                    definition = (
                        f"{sql_type} NOT NULL DEFAULT {default_sql}"
                    )

                elif column.primary_key:
                    print(
                        f"Skipped primary key {table_name}.{column.name}"
                    )
                    continue

                else:
                    print(
                        f"Skipped {table_name}.{column.name}: "
                        "required column has no safe default."
                    )
                    continue

                with db.engine.begin() as connection:
                    connection.execute(
                        text(
                            f'ALTER TABLE "{table_name}" '
                            f'ADD COLUMN "{column.name}" {definition}'
                        )
                    )

                print(f"Added {table_name}.{column.name}")

        print("\nDatabase schema repair finished.")
        print("Review any skipped columns before starting the app.")


if __name__ == "__main__":
    repair_database()