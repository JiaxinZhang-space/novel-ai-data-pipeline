# Public Repository Safety Policy

This repository accepts synthetic portfolio data only.

Do not commit or attach:

- real novel text, prompts, customer or author records;
- contracts, identity documents, payment records or platform screenshots;
- API keys, access tokens, private URLs or local credential files;
- production logs, databases, archives or unredacted evidence.

Run before every public push:

```bash
python scripts/check_public_repo.py
python -m unittest discover -s tests -v
```

The safety script is a lightweight guard and does not replace a human privacy, copyright or security review. Report non-sensitive bugs through GitHub Issues. Do not place sensitive details in a public issue; if a real secret is exposed, revoke it immediately and remove it from Git history before publishing.
