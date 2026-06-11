# Changelog

All notable changes to Memoria are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1](https://github.com/eranroseman/memoria-vault/compare/v0.3.0...v0.3.1) (2026-06-11)


### Bug Fixes

* **install,ci:** qmd bootstrap + {{QMD}} path substitution; CI hygiene (C9) ([#387](https://github.com/eranroseman/memoria-vault/issues/387)) ([be67d9b](https://github.com/eranroseman/memoria-vault/commit/be67d9bcadfde4888f7dca1ba929cb6567efd299))

## [0.3.0](https://github.com/eranroseman/memoria-vault/compare/v0.2.1...v0.3.0) (2026-06-11)


### Features

* **palette:** six per-task lane commands + pattern runner; deferred docs marked ([#203](https://github.com/eranroseman/memoria-vault/issues/203)) ([#388](https://github.com/eranroseman/memoria-vault/issues/388)) ([8ed00bb](https://github.com/eranroseman/memoria-vault/commit/8ed00bb64b2e76f89695bb646575b4e9a366d3b9))


### Bug Fixes

* **dashboards:** audit-log panels query the v0.1.1 gated zones; skill count 25 ([#395](https://github.com/eranroseman/memoria-vault/issues/395)) ([e17e59b](https://github.com/eranroseman/memoria-vault/commit/e17e59b0a703485e1393d19e82d1e9c4dc1369e8))

## [0.2.1](https://github.com/eranroseman/memoria-vault/compare/v0.2.0...v0.2.1) (2026-06-11)


### Bug Fixes

* **vault:** purge v0.1.0 remnants from shipped configs (A1-A4, A6, C8) ([#366](https://github.com/eranroseman/memoria-vault/issues/366)) ([3615436](https://github.com/eranroseman/memoria-vault/commit/36154366eb0b3e6c67c6854055aca81f6226ee02))

## [0.2.0](https://github.com/eranroseman/memoria-vault/compare/v0.1.0...v0.2.0) (2026-06-11)


### Features

* **acp:** route chat exports to notes/fleeting/chats and stamp them into fleeting triage ([#185](https://github.com/eranroseman/memoria-vault/issues/185)) ([#354](https://github.com/eranroseman/memoria-vault/issues/354)) ([8463b48](https://github.com/eranroseman/memoria-vault/commit/8463b48d96fa4324e3ad4bc8491f068d1f11bca9))
* add Harper grammar check (editor + CI + pre-commit advisory) ([#348](https://github.com/eranroseman/memoria-vault/issues/348)) ([8193e56](https://github.com/eranroseman/memoria-vault/commit/8193e56ee10449873c624889243a5c9a7b8c5c46))
* **board:** done-card raises a review work-prompt in the Inbox ([#341](https://github.com/eranroseman/memoria-vault/issues/341)) ([#357](https://github.com/eranroseman/memoria-vault/issues/357)) ([93b7e45](https://github.com/eranroseman/memoria-vault/commit/93b7e45cb899e493d7559045ab02d283a31ee5d2))
* **cluster:** cluster_emit_canvas — the claim-debate map ([#345](https://github.com/eranroseman/memoria-vault/issues/345)) ([#359](https://github.com/eranroseman/memoria-vault/issues/359)) ([f8e9a8b](https://github.com/eranroseman/memoria-vault/commit/f8e9a8be7b58093b30fd9c4a36116a698115f9b2))
* **eval:** activate vault-eval gold set, dispatch, and quarterly cron (ADR-11) ([#358](https://github.com/eranroseman/memoria-vault/issues/358)) ([04f6dfb](https://github.com/eranroseman/memoria-vault/commit/04f6dfb49e04a5320f272a06d018f4b1946026b1)), closes [#206](https://github.com/eranroseman/memoria-vault/issues/206)
* **ingest:** automate classification — audited, flag-on-ambiguity ([#335](https://github.com/eranroseman/memoria-vault/issues/335)) ([#355](https://github.com/eranroseman/memoria-vault/issues/355)) ([293b695](https://github.com/eranroseman/memoria-vault/commit/293b69570a5c94fbade1b6fb8d84b2b001f176c9))
* **palette:** add delegate-a-task and resolve-inbox-card commands ([#203](https://github.com/eranroseman/memoria-vault/issues/203)) ([#353](https://github.com/eranroseman/memoria-vault/issues/353)) ([7066e8b](https://github.com/eranroseman/memoria-vault/commit/7066e8baf12d5b504421a4a6ee089c8c5d110ee0))
* **skills:** Appendix-C skill registry — 26 skills, &lt;task&gt;:&lt;verb&gt;-&lt;object&gt; names ([#340](https://github.com/eranroseman/memoria-vault/issues/340)) ([#362](https://github.com/eranroseman/memoria-vault/issues/362)) ([26adcdd](https://github.com/eranroseman/memoria-vault/commit/26adcddf9bf7b145308f871dca9795bc991debaa))


### Bug Fixes

* **harper:** install pre-built binary instead of cargo compile ([#351](https://github.com/eranroseman/memoria-vault/issues/351)) ([079897b](https://github.com/eranroseman/memoria-vault/commit/079897b40ba16c7b35d1706e90b03f89a5c902b5))
* **install:** refresh mirrors authored .memoria infra (scoped rsync --delete) ([#363](https://github.com/eranroseman/memoria-vault/issues/363)) ([a42df0a](https://github.com/eranroseman/memoria-vault/commit/a42df0a277b1f0907ff1fe2ea4f673b5187e9dec))
* **install:** wire the pre-commit gate from --profiles-only too (D50) ([#360](https://github.com/eranroseman/memoria-vault/issues/360)) ([88820be](https://github.com/eranroseman/memoria-vault/commit/88820be81577f0dbb37c0805b565b74c4922a3ac))
* **mcp,linter:** Batch-2 code defects from the v0.1.1 review (B1-B7) ([#384](https://github.com/eranroseman/memoria-vault/issues/384)) ([8a7e873](https://github.com/eranroseman/memoria-vault/commit/8a7e8731e4698dafa7b9a363cc3ba12aeafa77a6))
* **policy:** MCP-only sandbox, no exceptions — D40/ADR-46 enforced literally ([#171](https://github.com/eranroseman/memoria-vault/issues/171)) ([#364](https://github.com/eranroseman/memoria-vault/issues/364)) ([8e71674](https://github.com/eranroseman/memoria-vault/commit/8e71674cc69a5eeed9c2658d4ca161a905204b66))
* **v0.1.1:** Zotero how-to group, metrics cron, installer banner ([#149](https://github.com/eranroseman/memoria-vault/issues/149), [#205](https://github.com/eranroseman/memoria-vault/issues/205)) ([#352](https://github.com/eranroseman/memoria-vault/issues/352)) ([ba49e47](https://github.com/eranroseman/memoria-vault/commit/ba49e47874dda85dd3820e778a014863e120dc51))


### Performance Improvements

* **linter:** prune SKIP_DIRS during the walk, not after rglob ([#361](https://github.com/eranroseman/memoria-vault/issues/361)) ([77d0a23](https://github.com/eranroseman/memoria-vault/commit/77d0a2375e2093116e901298f44913b7c2802b49))

## 0.1.0 (2026-06-09)


### Features

* ADR-27/28 gate enforcement, 99-system reorg, raw-note templates, dashboard+telemetry fixes ([76a0a3f](https://github.com/eranroseman/memoria-vault/commit/76a0a3f3a15161953cf6ac5d86685cd1b5f29a72))
* **ci:** gate auto-merge on clean Kilo Code Review ([#160](https://github.com/eranroseman/memoria-vault/issues/160)) ([68255fa](https://github.com/eranroseman/memoria-vault/commit/68255fa11a2b5779f39abc03a0379c98277bb389))
* **ci:** parse Kilo Code Review comment to gate on actual findings ([#163](https://github.com/eranroseman/memoria-vault/issues/163)) ([f673886](https://github.com/eranroseman/memoria-vault/commit/f673886ed50a231e338dd2e77510e583d70961ac))
* **docs-doctor:** enforce page-title link text; tidy AGENTS.md ([ddd97b1](https://github.com/eranroseman/memoria-vault/commit/ddd97b1ee9606a4b2bb36db2dd45dc0dc5795bde))
* **gate:** policy write-gate as a Hermes plugin, not a shell hook ([#58](https://github.com/eranroseman/memoria-vault/issues/58)) ([bfe07f0](https://github.com/eranroseman/memoria-vault/commit/bfe07f0513fb5c5f4b517e28210b2895a0113934))
* **ingest:** extract.py — Tier-1 full-text extraction (ADR-30) ([#98](https://github.com/eranroseman/memoria-vault/issues/98)) ([a7b32d4](https://github.com/eranroseman/memoria-vault/commit/a7b32d43c3e5bcf2572913ad57806611bbb28fd1))
* **ingest:** ingest_paper.py — Tier-0 of the ADR-30 pipeline ([#93](https://github.com/eranroseman/memoria-vault/issues/93)) ([278c695](https://github.com/eranroseman/memoria-vault/commit/278c695b3c4055ce66853d1640af887d43b2216d))
* **ingest:** link.py — Tier-1 deterministic linking (ADR-30) ([#97](https://github.com/eranroseman/memoria-vault/issues/97)) ([6bd3713](https://github.com/eranroseman/memoria-vault/commit/6bd3713e6e5dc39521581144e4ea3fa622ce1edd))
* **ingest:** pipeline.py — deterministic ingest orchestrator (ADR-30) ([#100](https://github.com/eranroseman/memoria-vault/issues/100)) ([b05159b](https://github.com/eranroseman/memoria-vault/commit/b05159b4f872dc1b58ae52a79d71949c28990d32))
* **ingest:** recover zotero_uri + pdf_uri from the BibTeX export (no Zotero API) ([#122](https://github.com/eranroseman/memoria-vault/issues/122)) ([afac183](https://github.com/eranroseman/memoria-vault/commit/afac1834c188d454fd6581c7d213b90a074f1684))
* **ingest:** resolve_merge.py — Tier-1 multi-source resolve + merge (ADR-30) ([#95](https://github.com/eranroseman/memoria-vault/issues/95)) ([8b6342d](https://github.com/eranroseman/memoria-vault/commit/8b6342d0acc9d83f683e5d997d9d85abe53e8a7e))
* **ingest:** sweeps.py — the two re-ingest backstops (ADR-30) ([#105](https://github.com/eranroseman/memoria-vault/issues/105)) ([ca5bebf](https://github.com/eranroseman/memoria-vault/commit/ca5bebf6f95a08f613136baddb5aa6972e4deba9))
* **ingest:** wire the re-ingest sweeps as a cron (ADR-30) ([#116](https://github.com/eranroseman/memoria-vault/issues/116)) ([811538b](https://github.com/eranroseman/memoria-vault/commit/811538bf3f7bd3b3c665029783a44a5d95d14d57))
* **installer:** create folder skeleton post-deploy, drop .keep placeholders ([#242](https://github.com/eranroseman/memoria-vault/issues/242)) ([50d48f4](https://github.com/eranroseman/memoria-vault/commit/50d48f41a2ac4a21a2a172376326adc2eec73d2e)), closes [#222](https://github.com/eranroseman/memoria-vault/issues/222)
* **librarian:** slim obsidian-paper-note SKILL.md to ADR-30 Option-A ([#103](https://github.com/eranroseman/memoria-vault/issues/103)) ([964fe1a](https://github.com/eranroseman/memoria-vault/commit/964fe1a43c7d918c1f484befd0c2830e96cff542))
* **librarian:** vault access via the native obsidian MCP over HTTP (ADR-31) ([#130](https://github.com/eranroseman/memoria-vault/issues/130)) ([c0cafb0](https://github.com/eranroseman/memoria-vault/commit/c0cafb0b82e4f983ac68258509cda793ebbb59dc))
* **linter:** misplaced-note detector + docs-doctor broken-vault-wikilink check ([#247](https://github.com/eranroseman/memoria-vault/issues/247)) ([d8ffa58](https://github.com/eranroseman/memoria-vault/commit/d8ffa58097e888756d9876d078160cc598d08e83))
* **obsidian:** ship workspaces.json; trim ACP picker seed ([#245](https://github.com/eranroseman/memoria-vault/issues/245)) ([d5887c9](https://github.com/eranroseman/memoria-vault/commit/d5887c98b829d9fac41bd550c02d12b77b34b7ff)), closes [#150](https://github.com/eranroseman/memoria-vault/issues/150) [#178](https://github.com/eranroseman/memoria-vault/issues/178)
* **profiles:** implement ADR-27 — gate enforces; obsidian is the only write path ([7cd8f14](https://github.com/eranroseman/memoria-vault/commit/7cd8f142c7cbb49f8c55d22afa571beada6732d3))
* **profiles:** native obsidian MCP on all seven lanes (ADR-31) ([#132](https://github.com/eranroseman/memoria-vault/issues/132)) ([77ad4ba](https://github.com/eranroseman/memoria-vault/commit/77ad4ba7bf1759325a09375c708f845ad45b246b))
* **quickadd:** implement Memoria: capture from Zotero selection ([#85](https://github.com/eranroseman/memoria-vault/issues/85)) ([d3d510d](https://github.com/eranroseman/memoria-vault/commit/d3d510d776e9b4241d55b893ccd44a6519474f4c))
* **quickadd:** new-project scaffold + card-producing lane triggers ([#249](https://github.com/eranroseman/memoria-vault/issues/249)) ([58777e6](https://github.com/eranroseman/memoria-vault/commit/58777e60003daa1a6bf6e27559d65cb352609746)), closes [#154](https://github.com/eranroseman/memoria-vault/issues/154) [#184](https://github.com/eranroseman/memoria-vault/issues/184)
* **telemetry:** timestamp lint findings + periodized lint-verdict notes; re-enrich drift-watch ([20caf42](https://github.com/eranroseman/memoria-vault/commit/20caf4204a969d09ed8321c85f0b81a4c2a4e32d))
* **telemetry:** wire the board-export cron (G5) ([8a13a88](https://github.com/eranroseman/memoria-vault/commit/8a13a8867e805fdad9b0d5a5a42ca776e5fa78fe))
* **vault:** seed 00-meta/vocabulary.md — controlled classification vocabulary ([#101](https://github.com/eranroseman/memoria-vault/issues/101)) ([761dd7e](https://github.com/eranroseman/memoria-vault/commit/761dd7ea2e3ab55c63a2234f4e4eb3f0ecacbaed))


### Bug Fixes

* **adr:** reconcile ADR-05 bib-gitignore and ADR-06 citekey string ([#260](https://github.com/eranroseman/memoria-vault/issues/260)) ([ce7f253](https://github.com/eranroseman/memoria-vault/commit/ce7f2536d283a9d29554a05edf6b287acedc18ca))
* align pr-policy + AGENTS.md with the project/ reorg ([#241](https://github.com/eranroseman/memoria-vault/issues/241)) ([e63e62a](https://github.com/eranroseman/memoria-vault/commit/e63e62aa76aebd6d3d507312ebaf96800f1eed17))
* audit path-traversal denials ([#214](https://github.com/eranroseman/memoria-vault/issues/214)) ([#240](https://github.com/eranroseman/memoria-vault/issues/240)) ([644a8da](https://github.com/eranroseman/memoria-vault/commit/644a8da13caea4b31c54612bf249e6af4081975a))
* **board-export:** normalize last_updated to ISO-8601 in card projections ([#75](https://github.com/eranroseman/memoria-vault/issues/75)) ([85f6b13](https://github.com/eranroseman/memoria-vault/commit/85f6b13b5405ac04f2338de038d2ac89b8930a5e))
* **ci:** clear installer-lint blockers on the ADR-27 PR ([8607f19](https://github.com/eranroseman/memoria-vault/commit/8607f1956aab0230053c52dbbc841dc6cb4a2ee8))
* **ci:** match Kilo's actual comment format in pr-policy gate ([#200](https://github.com/eranroseman/memoria-vault/issues/200)) ([ccdc045](https://github.com/eranroseman/memoria-vault/commit/ccdc0455ea7778a8727fd314d0bf6de2d27394f6))
* **ci:** trusted authors get needs_human for sensitive paths, not block ([425ce04](https://github.com/eranroseman/memoria-vault/commit/425ce04f52d92b2e9810c26f6514ee2a53aac59c))
* **ci:** use env vars in github-script to avoid JS injection from reason string ([8c417d7](https://github.com/eranroseman/memoria-vault/commit/8c417d7fd67299106a0f028b8e445609b6c5841c))
* complete ADR-31 native-MCP wiring (HTTP server + OBSIDIAN_MCP_PORT) ([#233](https://github.com/eranroseman/memoria-vault/issues/233)) ([d880bcb](https://github.com/eranroseman/memoria-vault/commit/d880bcb64a1aa66781d60e40b8297e97263ba8ae))
* **dashboards:** correct board-state + drift-watch queries to real schemas ([43fcf60](https://github.com/eranroseman/memoria-vault/commit/43fcf603174ca76b63b734bafd65d6e2169336d4))
* **dashboards:** correct daily-health queries to match real log/card schemas ([50d2e25](https://github.com/eranroseman/memoria-vault/commit/50d2e25eb9ee713ab0d60aa1262e704a41fb85cd))
* **dashboards:** guard dataviewjs log loaders against missing/empty files ([72d32e8](https://github.com/eranroseman/memoria-vault/commit/72d32e81ce42f0db821a42b293fcfc2508d743ca))
* **dashboards:** keep daily-health above the fold with compact empty states ([108bb2f](https://github.com/eranroseman/memoria-vault/commit/108bb2f7f1d42e2239fecbcfe7c79a7222dcbd34))
* **dashboards:** per-block setInterval self-refresh for io.load views ([#168](https://github.com/eranroseman/memoria-vault/issues/168)) ([#243](https://github.com/eranroseman/memoria-vault/issues/243)) ([6c09700](https://github.com/eranroseman/memoria-vault/commit/6c09700798dc4c56d0f40641efdd09d06c77ad2f))
* **docs:** add nav_order to overview pages — What Memoria is first ([9ab26fc](https://github.com/eranroseman/memoria-vault/commit/9ab26fc64dd70149258ecde1e3b60163463bb6a1))
* **docs:** correct audit.jsonl schema to match the code ([72f13d1](https://github.com/eranroseman/memoria-vault/commit/72f13d1c5bafff30cae1ee07156e686180c66b9a))
* **docs:** correct audit.jsonl schema to match the code ([c7c1e8a](https://github.com/eranroseman/memoria-vault/commit/c7c1e8a4a59d85d82b25a80069ed9b5302120c1e))
* **docs:** pretty permalinks so the vault's trailing-slash page links resolve ([1214997](https://github.com/eranroseman/memoria-vault/commit/12149977d47f7d4852bf214b93eae3338de5ef55))
* **docs:** quote linter.md title; guard against unquoted-colon titles ([#36](https://github.com/eranroseman/memoria-vault/issues/36)) ([fc5fce0](https://github.com/eranroseman/memoria-vault/commit/fc5fce0639dc2aa5f6a8a4c208e857731f53ab88))
* **docs:** rename reference/kanban-board title to break sidebar clash ([#35](https://github.com/eranroseman/memoria-vault/issues/35)) ([0d23af4](https://github.com/eranroseman/memoria-vault/commit/0d23af477ba965b61598f9d9c7369fd3f47070e4))
* **docs:** rename reference/profiles.md title to break sidebar clash ([#34](https://github.com/eranroseman/memoria-vault/issues/34)) ([cbfee0c](https://github.com/eranroseman/memoria-vault/commit/cbfee0ccb7ae3e6bf3daf6635aeb3b12ebf4b404))
* **docs:** resolve cross-file contradictions and subtle inconsistencies ([b680896](https://github.com/eranroseman/memoria-vault/commit/b680896765557c34bf16599a09718b9d4d8f3bb5))
* **docs:** restore ~/.hermes runtime paths corrupted by the rename regex ([#42](https://github.com/eranroseman/memoria-vault/issues/42)) ([80f373c](https://github.com/eranroseman/memoria-vault/commit/80f373c5d045c9ea940dfb2a7090d19ad2f1c81a))
* **docs:** use the no-slash Pages URL form so vault links resolve (was 404) ([f191962](https://github.com/eranroseman/memoria-vault/commit/f191962175633e1ba4bbff1c6fb76a2555a6ce0a))
* **docs:** use the no-slash Pages URL form so vault links resolve (was 404) ([2d2366a](https://github.com/eranroseman/memoria-vault/commit/2d2366ad7438f0ce8ed1918b63ca466566662743))
* **gate:** correct hook matcher (fullmatch) + seed keys into each profile .env ([3e5d703](https://github.com/eranroseman/memoria-vault/commit/3e5d703522da30c613a124948e7b5bb5e7bf800d))
* **ingest:** complete metadata — promote API IDs, recover PDF, extract via PMCID ([#119](https://github.com/eranroseman/memoria-vault/issues/119)) ([29cb070](https://github.com/eranroseman/memoria-vault/commit/29cb070c39e2194257f7d6ea0e1835cb23037390))
* **ingest:** deliver the pipeline as an MCP tool; resolve vault from env ([#110](https://github.com/eranroseman/memoria-vault/issues/110)) ([00b3aed](https://github.com/eranroseman/memoria-vault/commit/00b3aed87b45c10af8e8c0913af82ca187e11eb5))
* **ingest:** make entity note paths deterministically ID-keyed ([#121](https://github.com/eranroseman/memoria-vault/issues/121)) ([ea4f572](https://github.com/eranroseman/memoria-vault/commit/ea4f572c84af5c1778b75d3977eed21119ab6d73))
* **ingest:** persist the full-text extract (90-assets is outside the agent lane) ([#120](https://github.com/eranroseman/memoria-vault/issues/120)) ([13b5f64](https://github.com/eranroseman/memoria-vault/commit/13b5f6434b5ab5bea5591c8df135d7221f1281bd))
* **ingest:** S2 429-retry in _get + capture-intake anchor backstop in the tool ([#114](https://github.com/eranroseman/memoria-vault/issues/114)) ([fef67d8](https://github.com/eranroseman/memoria-vault/commit/fef67d83680cb2be18f6835820c11d4c1ca30ecf))
* **ingest:** sandbox PDF parsing in a resource-limited subprocess (ADR-30) ([#262](https://github.com/eranroseman/memoria-vault/issues/262)) ([e68ca3c](https://github.com/eranroseman/memoria-vault/commit/e68ca3cf3f8a7ebd1f04da37d1b7f0d287374a17))
* **install.ps1:** wslpath backslash stripping; stderr-as-error abort ([a0e71de](https://github.com/eranroseman/memoria-vault/commit/a0e71ded48ebf0bb6e28d10994332638495af487))
* **install.sh:** correct profile-install syntax, non-interactive skills, exit 0 ([#6](https://github.com/eranroseman/memoria-vault/issues/6)) ([b0aa222](https://github.com/eranroseman/memoria-vault/commit/b0aa222ff45f680a278cc63bb79e48d70dd6c5f6))
* **install.sh:** don't let empty profile .env keys shadow the global key ([#32](https://github.com/eranroseman/memoria-vault/issues/32)) ([a6a7ce9](https://github.com/eranroseman/memoria-vault/commit/a6a7ce9c0be887e920c60f6f965b33c7f9284087))
* **install.sh:** EXIT trap returning 1 on success; dry-run mcp-deps message ([cb1f7c5](https://github.com/eranroseman/memoria-vault/commit/cb1f7c5584f4cbf2bc79b7239a1170fb895eccc7))
* **install.sh:** robust venv (ensurepip prereq + working fallback) ([#5](https://github.com/eranroseman/memoria-vault/issues/5)) ([5a82936](https://github.com/eranroseman/memoria-vault/commit/5a82936b3c05ba0c78b419256073d88773717f92))
* **install:** bundled official skills are verified, not hub-installed ([#59](https://github.com/eranroseman/memoria-vault/issues/59)) ([36c9130](https://github.com/eranroseman/memoria-vault/commit/36c91300fcce08e2a11f2dfbb9a4af88094dd931))
* **installer:** substitute {{HOME}} + set windowsWslMode when seeding agent-client ([#74](https://github.com/eranroseman/memoria-vault/issues/74)) ([b15dde8](https://github.com/eranroseman/memoria-vault/commit/b15dde898b9fc9e9c116f6f3857afbd3b1c4b1e3))
* **installer:** write disabled_toolsets as a real YAML list ([#51](https://github.com/eranroseman/memoria-vault/issues/51), Tier-3 finding) ([3aa7561](https://github.com/eranroseman/memoria-vault/commit/3aa7561b22a4c564cf12521c76a7fb42b71fc0a5))
* **install:** seed agent-client/data.json + install Git for Windows ([0691c1f](https://github.com/eranroseman/memoria-vault/commit/0691c1fb9e3ce4abbcfd222bb9718840cab297c0))
* **linter SOUL:** de-link docs/ ref + correct two stale doc filenames ([#22](https://github.com/eranroseman/memoria-vault/issues/22)) ([9099ae2](https://github.com/eranroseman/memoria-vault/commit/9099ae2470f0c333b6a4b58a5c94ae455021ea60))
* **linter:** stop the 15 false positives from the 99-system template move ([#76](https://github.com/eranroseman/memoria-vault/issues/76)) ([f023f7a](https://github.com/eranroseman/memoria-vault/commit/f023f7a2e337f44fbe12a3218d4fe298b7fe5ff4))
* **mapper:** retire dead clustering skill grants; mark clustering deferred (ADR-33) ([#261](https://github.com/eranroseman/memoria-vault/issues/261)) ([0a6702b](https://github.com/eranroseman/memoria-vault/commit/0a6702b6c2470e2ed509e605d9b289486a67df40))
* **obsidian:** enable the homepage plugin on install ([#129](https://github.com/eranroseman/memoria-vault/issues/129)) ([8a8d958](https://github.com/eranroseman/memoria-vault/commit/8a8d9584e6d956cb6bfa68e3ebfed07d723794c0))
* **pages:** add explicit permalink to all section READMEs ([#15](https://github.com/eranroseman/memoria-vault/issues/15)) ([c248eff](https://github.com/eranroseman/memoria-vault/commit/c248effce8c662fa8b501b9c37dc34bf4ff82307))
* path traversal in policy gate, API key in URL, citekey sanitization ([#218](https://github.com/eranroseman/memoria-vault/issues/218)) ([797b706](https://github.com/eranroseman/memoria-vault/commit/797b7060260a53d1376395b09564127d057654f4))
* **policy:** resolve obsidian-bridge ([#39](https://github.com/eranroseman/memoria-vault/issues/39)) and gate-bypass ([#51](https://github.com/eranroseman/memoria-vault/issues/51)) Tier-4 blockers ([c5b8709](https://github.com/eranroseman/memoria-vault/commit/c5b87091b858f86bdd223a704f7f815a19c1c958))
* **profiles:** align env_requires with the keys skills actually read ([#71](https://github.com/eranroseman/memoria-vault/issues/71)) ([9e14825](https://github.com/eranroseman/memoria-vault/commit/9e14825a4678a94df7d398767a8a644780d9bfb6))
* **project:** repair 59 reorg-broken cross-links; widen status-doctor to all of project/ ([#271](https://github.com/eranroseman/memoria-vault/issues/271)) ([b4c73ce](https://github.com/eranroseman/memoria-vault/commit/b4c73cec058223fa7579c644b05952729fcf453a))
* **quickadd:** add the capture-intake durability anchor to the macro ([#127](https://github.com/eranroseman/memoria-vault/issues/127)) ([8dcc436](https://github.com/eranroseman/memoria-vault/commit/8dcc436547d1bb7807c42ce249865b0ce5cc18e5))
* re-activate check-test-refs (stale project-files/tests path) ([#234](https://github.com/eranroseman/memoria-vault/issues/234)) ([9c0769a](https://github.com/eranroseman/memoria-vault/commit/9c0769a241556d628257e0a78136b27fa57a121e))
* restore pip Dependabot; the dropped bumps were valid ([#238](https://github.com/eranroseman/memoria-vault/issues/238)) ([dc9f84d](https://github.com/eranroseman/memoria-vault/commit/dc9f84dbd34c53dd6494e1e5f9d9663cff0fd5bc))
* **scripts:** update installer self-references after the move to scripts/ ([46b1773](https://github.com/eranroseman/memoria-vault/commit/46b17734ac9100dff974cab1e87c9a045efbaf69))
* surface silently swallowed errors to stderr across vault tooling ([#216](https://github.com/eranroseman/memoria-vault/issues/216)) ([a873697](https://github.com/eranroseman/memoria-vault/commit/a87369784e1d02a3aa816b5f65e519d896f5229c))
* **test.sh:** correct stale detectors path; add verify_mcp self-test ([#284](https://github.com/eranroseman/memoria-vault/issues/284)) ([e8789f7](https://github.com/eranroseman/memoria-vault/commit/e8789f7b5a8ab40213ececfcabd5d66f5280da13))
* **vault:** last stale docs/ refs — drift-watch plugins.md + 7 lane-override blobs ([#29](https://github.com/eranroseman/memoria-vault/issues/29)) ([0769f60](https://github.com/eranroseman/memoria-vault/commit/0769f60cf006ac2276e3c2a1c1e2d41b55be8096))
* **vault:** replace relative docs/ links with GitHub Pages URLs ([#19](https://github.com/eranroseman/memoria-vault/issues/19)) ([0add5f8](https://github.com/eranroseman/memoria-vault/commit/0add5f8b8c650c46fddb735284f5e7d62eef2f26))
* **vault:** replace remaining stale companion-line doc paths with URLs ([#28](https://github.com/eranroseman/memoria-vault/issues/28)) ([bf859d2](https://github.com/eranroseman/memoria-vault/commit/bf859d21c862724320202111f69ad036f472109a))
* **vault:** replace stale doc paths with website URLs in 00-meta ([#23](https://github.com/eranroseman/memoria-vault/issues/23)) ([b423150](https://github.com/eranroseman/memoria-vault/commit/b42315041fa168079b6236ea3deee1e02dc84c7c))

## [Unreleased]

Working toward the first tagged release, **v0.1.0** — **not yet cut.** No
`v0.1.0` tag or GitHub release exists; see the release gate in
[project/release/v0.1/release-plan-v0.1.md](docs/releasing/v0.1/release-plan-v0.1.md).

### Added
- Seven specialist agent profiles: `librarian`, `mapper`, `socratic`, `writer`, `verifier`, `coder`, `linter`
- Obsidian starter vault (`vault/`) with the `.memoria/` tooling layer; Diátaxis engineering docs in `docs/`
- `scripts/install.sh` (Ubuntu/WSL2 bootstrap) and `scripts/install.ps1` (thin Windows → WSL2 launcher)
- Policy MCP write-gate + `policy_hook.py` pre/post tool-call hook (the structural review gate)
- Six-signal telemetry capture (`board_export.py`, `metrics_aggregate.py`, Linter `detectors.py`)
- Deterministic ingest pipeline ([ADR-30](docs/adr/30-deterministic-ingest-pipeline.md)): capture → fallback-chained enrichment (Semantic Scholar + OpenAlex + Crossref, per-field best-source merge) → full-text extraction (PMC / local Zotero PDF via `pymupdf4llm`) → ID-keyed entity + citation linking → gated write. Delivered as the `ingest_pipeline` MCP tool (the worker can't exec scripts); the Librarian makes only two judgments — a `vocabulary.md`-constrained classification proposal and a comparative `[!brief]`. Adds the `captured` lifecycle + `ingest_status` fields, a seeded `00-meta/vocabulary.md`, the capture-intake durability log, and two re-ingest backstop sweeps on cron. Zotero-native fields (`zotero_uri`/`pdf_uri`) come from the Better BibTeX export — no live Zotero API. (#92–#123)
- CI required checks: `docs-doctor`, `shellcheck (scripts/install.sh)`, `PSScriptAnalyzer (scripts/install.ps1)`, `python-selftest`, `docs-links`
- Repo health: GitHub issue/PR templates, `CODEOWNERS`, `FUNDING.yml`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `LICENSE` (MIT), and `AGENTS.md` (agent workflow guidelines)

### Fixed

- Obsidian MCP bridge now receives its API key in live Hermes runs
  ([#39](https://github.com/eranroseman/memoria-vault/issues/39)) — the prior
  v0.1 release blocker; live HTTP 204 vault write confirmed (see ADR-27).

[Unreleased]: https://github.com/eranroseman/memoria-vault/commits/main
