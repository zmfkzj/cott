package cott_impl.curriculum.effects_selection

internal fun store_and_load(database: java.nio.file.Path, key: kotlin.String, `value`: kotlin.String): cott_runtime.CottResult<kotlin.String, curriculum.effects_selection.EffectError> {
    return try {
        val stored = java.sql.DriverManager.getConnection("jdbc:sqlite:" + database.toAbsolutePath().toString()).use { connection ->
            connection.autoCommit = false
            try {
                connection.createStatement().use { statement ->
                    statement.executeUpdate("CREATE TABLE IF NOT EXISTS cott_key_value (key TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)")
                }
                connection.prepareStatement("INSERT INTO cott_key_value (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value").use { statement ->
                    statement.setString(1, key)
                    statement.setString(2, value)
                    statement.executeUpdate()
                }
                val loaded = connection.prepareStatement("SELECT value FROM cott_key_value WHERE key = ?").use { statement ->
                    statement.setString(1, key)
                    statement.executeQuery().use { rows ->
                        if (!rows.next()) {
                            throw java.sql.SQLException("Stored key was not found")
                        }
                        rows.getString(1) ?: throw java.sql.SQLException("Stored value was null")
                    }
                }
                if (loaded != value) {
                    throw java.sql.SQLException("Stored value did not match the supplied value")
                }
                connection.commit()
                loaded
            } catch (failure: kotlin.Exception) {
                try {
                    connection.rollback()
                } catch (rollbackFailure: kotlin.Exception) {
                    failure.addSuppressed(rollbackFailure)
                }
                throw failure
            }
        }
        cott_runtime.Ok(stored)
    } catch (failure: kotlin.Exception) {
        cott_runtime.Err(curriculum.effects_selection.EffectError.OperationFailed(failure.message ?: "SQLite store and load failed"))
    }
}
