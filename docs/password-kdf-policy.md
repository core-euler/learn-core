# Password/KDF Policy (Production)

## Active policy

Пароли хешируются по policy, задаваемой через env/config:

- `PASSWORD_KDF_ALGORITHM=scrypt|argon2id` (default: `scrypt`)
- Для `scrypt`:
  - `PASSWORD_SCRYPT_N` (default `16384`)
  - `PASSWORD_SCRYPT_R` (default `8`)
  - `PASSWORD_SCRYPT_P` (default `1`)
  - `PASSWORD_SCRYPT_DKLEN` (default `64`)
  - `PASSWORD_SCRYPT_SALT_BYTES` (default `16`)
- Для `argon2id`:
  - `PASSWORD_ARGON2_TIME_COST` (default `3`)
  - `PASSWORD_ARGON2_MEMORY_COST_KIB` (default `65536`)
  - `PASSWORD_ARGON2_PARALLELISM` (default `2`)
  - `PASSWORD_ARGON2_HASH_LEN` (default `32`)
  - `PASSWORD_ARGON2_SALT_BYTES` (default `16`)

Форматы хранения:
- `scrypt$N$r$p$dklen$salt_b64$hash_b64`
- `argon2id$time$memory_kib$parallelism$hash_len$salt_b64$hash_b64`

## Migration strategy (legacy hashes)

Исторический формат (`salt$sha256(salt+password)`) поддерживается только для верификации при логине и не используется для новых регистраций.

Параметры миграции:
- `PASSWORD_LEGACY_ACCEPT=true|false` (default: `true`)
- `PASSWORD_MIGRATE_ON_LOGIN=true|false` (default: `true`)

Поведение:
1. Пользователь логинится со старым hash.
2. При успешной проверке пароль immediately rehash-ится по текущей policy (`PASSWORD_KDF_ALGORITHM`).
3. В БД записывается новый hash-format.
4. Следующие логины используют только новый KDF.

Рекомендации для production rollout:
1. Включить `PASSWORD_LEGACY_ACCEPT=true` + `PASSWORD_MIGRATE_ON_LOGIN=true` на период миграции.
2. Мониторить долю legacy hash в users table.
3. После миграционного окна выставить `PASSWORD_LEGACY_ACCEPT=false`.
