-- Replace this with your actual activation + password reset SQL.
-- The app only passes {USERID} as a variable.
-- Example pattern:
-- UPDATE [user]
-- SET UserActive = 1,
--     Password = 'Reset@123',
--     PasswordChanged = 1
-- WHERE userid = '{USERID}';

UPDATE [dbo].[user]
SET UserActive = 2,
    PasswordHash = 'Welcome@123'
WHERE userid = '{USERID}';


