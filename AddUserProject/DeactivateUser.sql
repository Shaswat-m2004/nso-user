-- Replace this with your actual deactivation SQL.
-- The app only passes {USERID} as a variable.
-- Example pattern:
-- UPDATE [user]
-- SET UserActive = 0
-- WHERE userid = '{USERID}';

UPDATE [dbo].[user]
SET UserActive = '1'
WHERE userid = '{USERID}'
  
  AND company = '100'
  AND division = '200';
