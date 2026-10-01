# Bulk-upload reference data

`material_bulk_upload.csv` and `container_bulk_upload.csv` document the expected
column contracts. The bulk-upload tests construct run-specific CSV payloads from
these references instead of uploading shared fixed records directly.

Keep reference inputs here; put generated output under `reports/` or temporary
storage, not alongside source fixtures.
