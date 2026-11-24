# user-auth delta

## REMOVED Requirements

### Requirement: Password hashing

The system SHALL store user passwords as salted scrypt hashes and SHALL verify them without revealing the stored hash.

#### Scenario: Hash round-trip

- **WHEN** a password is hashed and later verified with the same password
- **THEN** verification succeeds; verification with a different password fails

## ADDED Requirements

### Requirement: Password encryption with a server key

The system SHALL store user passwords reversibly encrypted with the server key `PASSWORD_KEY` from the environment and SHALL verify a supplied password by decrypting the stored value. The key and the generated password file SHALL NOT be committed to the repository or baked into container images.

#### Scenario: Encryption round-trip

- **WHEN** a password is encrypted and later verified with the same password
- **THEN** verification succeeds; verification with a different password fails

#### Scenario: Tampered value rejected

- **WHEN** the stored encrypted value is modified or was encrypted with another key
- **THEN** verification fails

#### Scenario: Missing key

- **WHEN** a password operation runs without `PASSWORD_KEY`
- **THEN** the system fails with a clear configuration error instead of storing or accepting a password

#### Scenario: Legacy hashes rejected

- **WHEN** the stored value uses the old `scrypt` format
- **THEN** verification fails and the user must receive a new password through the reset procedure

### Requirement: Bulk password reset

The system SHALL provide a script that generates new random passwords for all existing users, stores them encrypted with `PASSWORD_KEY`, revokes active refresh tokens, and writes the logins and plaintext passwords to a git-ignored file readable only by the owner.

#### Scenario: Reset all users

- **WHEN** an operator runs the reset script with `PASSWORD_KEY` set
- **THEN** every user receives a new encrypted password and the script writes the login/password pairs to the configured file

#### Scenario: Missing key on reset

- **WHEN** the reset script runs without `PASSWORD_KEY`
- **THEN** it exits with a configuration error and changes no passwords

#### Scenario: Credentials file is not committed

- **WHEN** the reset script writes the credentials file
- **THEN** the file lives in a git-ignored directory with owner-only permissions
