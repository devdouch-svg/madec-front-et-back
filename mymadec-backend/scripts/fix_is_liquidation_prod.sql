-- Fix prod when is_liquidation column is missing (mobile home 500).
-- Run on mymadec database (SSMS, sqlcmd, or via SSH tunnel on port 1433).

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.products')
      AND name = N'is_liquidation'
)
BEGIN
    ALTER TABLE dbo.products
        ADD is_liquidation BIT NOT NULL
            CONSTRAINT DF_products_is_liquidation DEFAULT 0;
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'ix_products_is_liquidation'
      AND object_id = OBJECT_ID(N'dbo.products')
)
BEGIN
    CREATE INDEX ix_products_is_liquidation ON dbo.products (is_liquidation);
END
GO

-- If Alembic is stuck before 006, stamp after running this script:
-- docker exec backend-api-1 alembic stamp 006
