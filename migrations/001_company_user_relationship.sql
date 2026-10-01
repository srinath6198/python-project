-- Run once before deploying the non-null User.company_id model.
-- Existing users without a company are isolated into individual legacy companies.
INSERT INTO companies (
    company_code,
    company_name,
    is_active,
    created_at,
    updated_at
)
SELECT
    CONCAT('LEGACY-', user_id),
    COALESCE(NULLIF(shopName, ''), NULLIF(full_name, ''), CONCAT('Legacy company ', user_id)),
    1,
    UTC_TIMESTAMP(),
    UTC_TIMESTAMP()
FROM users
WHERE company_id IS NULL;

UPDATE users AS u
JOIN companies AS c ON c.company_code = CONCAT('LEGACY-', u.user_id)
SET u.company_id = c.company_id
WHERE u.company_id IS NULL;

ALTER TABLE users
MODIFY company_id INT NOT NULL;