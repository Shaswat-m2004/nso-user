SELECT
    userid,
    username,
    UserActive,
    GroupID,
    company,
    division,
    WarehouseID
FROM [dbo].[user] WITH (NOLOCK)
WHERE GroupID = 'manager'
  AND company = '100'
  AND division = '200'
  AND UserActive = '2'
ORDER BY WarehouseID, userid;