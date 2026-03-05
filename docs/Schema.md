| table_name         | column_name     | data_type                |
| ------------------ | --------------- | ------------------------ |
| evaluation_history | id              | uuid                     |
| evaluation_history | user_id         | uuid                     |
| evaluation_history | title           | text                     |
| evaluation_history | evaluation_type | text                     |
| evaluation_history | resume_filename | text                     |
| evaluation_history | resume_url      | text                     |
| evaluation_history | resume_text     | text                     |
| evaluation_history | result_data     | jsonb                    |
| evaluation_history | overall_score   | numeric                  |
| evaluation_history | trust_score     | numeric                  |
| evaluation_history | created_at      | timestamp with time zone |
| evaluation_history | updated_at      | timestamp with time zone |
| evaluation_history | is_archived     | boolean                  |
| evaluation_history | archived_at     | timestamp with time zone |
| recent_evaluations | id              | uuid                     |
| recent_evaluations | user_id         | uuid                     |
| recent_evaluations | title           | text                     |
| recent_evaluations | evaluation_type | text                     |
| recent_evaluations | resume_filename | text                     |
| recent_evaluations | overall_score   | numeric                  |
| recent_evaluations | trust_score     | numeric                  |
| recent_evaluations | created_at      | timestamp with time zone |
| recent_evaluations | is_archived     | boolean                  |
| user_profiles      | id              | uuid                     |
| user_profiles      | email           | text                     |
| user_profiles      | full_name       | text                     |
| user_profiles      | avatar_url      | text                     |
| user_profiles      | role            | text                     |
| user_profiles      | company         | text                     |
| user_profiles      | job_title       | text                     |
| user_profiles      | phone           | text                     |
| user_profiles      | is_active       | boolean                  |
| user_profiles      | email_verified  | boolean                  |
| user_profiles      | last_login_at   | timestamp with time zone |
| user_profiles      | created_at      | timestamp with time zone |
| user_profiles      | updated_at      | timestamp with time zone |

| table_schema | table_name | column_name                 | data_type                | is_nullable |
| ------------ | ---------- | --------------------------- | ------------------------ | ----------- |
| auth         | users      | instance_id                 | uuid                     | YES         |
| auth         | users      | id                          | uuid                     | NO          |
| auth         | users      | aud                         | character varying        | YES         |
| auth         | users      | role                        | character varying        | YES         |
| auth         | users      | email                       | character varying        | YES         |
| auth         | users      | encrypted_password          | character varying        | YES         |
| auth         | users      | email_confirmed_at          | timestamp with time zone | YES         |
| auth         | users      | invited_at                  | timestamp with time zone | YES         |
| auth         | users      | confirmation_token          | character varying        | YES         |
| auth         | users      | confirmation_sent_at        | timestamp with time zone | YES         |
| auth         | users      | recovery_token              | character varying        | YES         |
| auth         | users      | recovery_sent_at            | timestamp with time zone | YES         |
| auth         | users      | email_change_token_new      | character varying        | YES         |
| auth         | users      | email_change                | character varying        | YES         |
| auth         | users      | email_change_sent_at        | timestamp with time zone | YES         |
| auth         | users      | last_sign_in_at             | timestamp with time zone | YES         |
| auth         | users      | raw_app_meta_data           | jsonb                    | YES         |
| auth         | users      | raw_user_meta_data          | jsonb                    | YES         |
| auth         | users      | is_super_admin              | boolean                  | YES         |
| auth         | users      | created_at                  | timestamp with time zone | YES         |
| auth         | users      | updated_at                  | timestamp with time zone | YES         |
| auth         | users      | phone                       | text                     | YES         |
| auth         | users      | phone_confirmed_at          | timestamp with time zone | YES         |
| auth         | users      | phone_change                | text                     | YES         |
| auth         | users      | phone_change_token          | character varying        | YES         |
| auth         | users      | phone_change_sent_at        | timestamp with time zone | YES         |
| auth         | users      | confirmed_at                | timestamp with time zone | YES         |
| auth         | users      | email_change_token_current  | character varying        | YES         |
| auth         | users      | email_change_confirm_status | smallint                 | YES         |
| auth         | users      | banned_until                | timestamp with time zone | YES         |
| auth         | users      | reauthentication_token      | character varying        | YES         |
| auth         | users      | reauthentication_sent_at    | timestamp with time zone | YES         |
| auth         | users      | is_sso_user                 | boolean                  | NO          |
| auth         | users      | deleted_at                  | timestamp with time zone | YES         |
| auth         | users      | is_anonymous                | boolean                  | NO          |