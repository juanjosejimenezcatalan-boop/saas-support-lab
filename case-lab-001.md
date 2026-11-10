# LAB-001 · Study missing from the portal

**Reported issue.** A clinic reported that study `LAB-001` did not appear in the portal after upload. This is a simulated incident with fictional data.

**Investigation.** I queried PostgreSQL and confirmed that the study was recorded as `received`. I joined the study record with its event history and found a `validation_failed` event. Filtering the validation log by `LAB-001` showed `missing_field=accession_number` at `09:14:03`.

**Diagnosis.** The upload was accepted, but the study could not proceed to publication because the accession number was missing.

**Customer response.** We received study `LAB-001`, but it could not be processed because the accession number was missing. Please check the accession number in the source system and resend the study after correcting it.

**Verification.** After simulating the corrected resubmission, I confirmed in PostgreSQL that the study status was `published`. The event history retained the original validation failure and showed the subsequent successful validation and publication. In a live incident, I would also verify that the study is visible with the clinic’s permissions.
