# User stories and acceptance criteria

**US-1: Sync field data.** As a data analyst, I want submitted forms copied into SQL so I can report on them.
- Given new submissions in CommCare, when the sync runs, then only forms received since the last sync are fetched.
- Re-running the sync creates no duplicate rows.

**US-2: Trust the data.** As a program manager, I want bad records flagged so I can ask teams to correct them.
- Records with a missing site, invalid household size, or inconsistent counts appear in `dq_issue` with a reason.
- Checks can be re-run at any time and reflect current data.

**US-3: Safe configuration.** As a security-conscious developer, I want credentials kept out of the code.
- API credentials are read from environment variables only.
- Database files and `.env` are git-ignored.

**US-4: Verified changes.** As a maintainer, I want automated tests so changes do not break the pipeline.
- CI runs the unit tests and a synthetic end-to-end run on every push.
