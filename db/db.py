import os
import random
import time

from .schema import db


def init_db(app):
    app.logger.info(
        f"Initializing database with URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')}"
    )

    db.init_app(app)

    # Extract database path from URI for file-based locking
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///"):
        db_path = db_uri.replace("sqlite:///", "")
        lock_file = f"{db_path}.lock"
    else:
        lock_file = "/tmp/db_init.lock"

    # Use file locking to prevent race conditions
    max_retries = 10
    for attempt in range(max_retries):
        try:
            if os.path.exists(lock_file):
                app.logger.info(
                    f"Database initialization lock exists, waiting... (attempt {attempt + 1})"
                )
                time.sleep(
                    random.uniform(0.1, 0.5)
                )  # Random delay to avoid thundering herd
                continue

            # Create lock file
            with open(lock_file, "w") as f:
                f.write(str(os.getpid()))

            app.logger.info("Acquired database initialization lock")

            with app.app_context():
                app.logger.info("Creating database tables...")

                # Check if we need to handle missing columns in existing tables
                try:
                    from sqlalchemy import text

                    # Check if created_at column exists in document table
                    pragma_result = db.session.execute(
                        text("PRAGMA table_info(document);")
                    ).fetchall()
                    columns = [
                        column[1] for column in pragma_result
                    ]  # column[1] is the column name
                    app.logger.info(f"Document table columns: {columns}")

                    if "created_at" not in columns and len(columns) > 0:
                        app.logger.warning(
                            "Document table exists but missing created_at column. Recreating database..."
                        )
                        db.drop_all()
                        app.logger.info("Dropped existing tables")

                    # Check if Google OAuth columns exist in user table
                    user_pragma = db.session.execute(
                        text("PRAGMA table_info(user);")
                    ).fetchall()
                    user_columns = [column[1] for column in user_pragma]
                    app.logger.info(f"User table columns: {user_columns}")

                    if len(user_columns) > 0 and "google_id" not in user_columns:
                        app.logger.info("Adding Google OAuth columns to user table...")
                        db.session.execute(
                            text(
                                "ALTER TABLE user ADD COLUMN google_id VARCHAR(128) UNIQUE"
                            )
                        )
                        db.session.execute(
                            text(
                                "ALTER TABLE user ADD COLUMN google_email VARCHAR(128)"
                            )
                        )
                        db.session.execute(
                            text(
                                "ALTER TABLE user ADD COLUMN auth_provider VARCHAR(32) DEFAULT 'local'"
                            )
                        )
                        db.session.commit()
                        app.logger.info("Successfully added Google OAuth columns")

                except Exception as e:
                    app.logger.info(
                        f"Could not check existing schema (probably no tables exist yet): {e!s}"
                    )

                # Create tables with error handling
                try:
                    db.create_all()
                    app.logger.info("Successfully created/verified database tables")
                except Exception as e:
                    if "already exists" in str(e):
                        app.logger.info("Tables already exist, continuing...")
                    else:
                        raise

                # Test database connection
                try:
                    result = db.session.execute(
                        text('SELECT name FROM sqlite_master WHERE type="table";')
                    ).fetchall()
                    app.logger.info(
                        f"Database tables found: {[row[0] for row in result]}"
                    )

                    # Check User table specifically
                    user_count = db.session.execute(
                        text("SELECT COUNT(*) FROM user")
                    ).fetchone()[0]
                    app.logger.info(f"Current user count in database: {user_count}")

                    # Verify Document table has created_at column
                    pragma_result = db.session.execute(
                        text("PRAGMA table_info(document);")
                    ).fetchall()
                    columns = [column[1] for column in pragma_result]
                    app.logger.info(f"Final Document table columns: {columns}")

                except Exception as e:
                    app.logger.error(f"Database test failed: {e!s}")

            break  # Success, exit retry loop

        except Exception as e:
            app.logger.error(
                f"Database initialization failed (attempt {attempt + 1}): {e!s}"
            )
            if attempt == max_retries - 1:
                raise
            time.sleep(random.uniform(0.1, 0.5))
        finally:
            # Always remove lock file if we created it
            try:
                if os.path.exists(lock_file):
                    with open(lock_file) as f:
                        lock_pid = f.read().strip()
                    if lock_pid == str(os.getpid()):
                        os.remove(lock_file)
                        app.logger.info("Released database initialization lock")
            except Exception as e:
                app.logger.warning(f"Failed to remove lock file: {e!s}")

    app.logger.info("Database initialization completed")
