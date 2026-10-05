# Stack Discovery Checklist

Run before the first change in an unfamiliar repository. **Verify by executing,
never by assuming.** A wrong command is worse than no command — the agent will
run it, fail, and improvise.

## 1. What is this
- Manifest files: `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`,
  `pom.xml`, `build.gradle`, `Gemfile`, `*.csproj`, `composer.json`
- Runtime version pins: `.tool-versions`, `.nvmrc`, `.python-version`,
  `Dockerfile`, CI matrix
- Monorepo? Workspace config, `nx.json`, `turbo.json`, `pnpm-workspace.yaml`

## 2. How it runs
- Checked-in wrappers first: `./gradlew`, `./mvnw`, `make`, `just`, `./scripts/*`
- Container: `docker-compose*.yml`, `.devcontainer/`
- Configuration and required environment: `.env.example`, config directory
- **Run the setup and the test command. Record what actually worked.**

## 3. How it is verified
- Test directories, file naming, and how a *single* test is run
- Test tiers: fast vs integration vs e2e; which one gates merges
- Lint, format, type-check commands; pre-commit hooks
- CI workflow — the authoritative list of what must pass

## 4. How it is shaped
- Top-level directories and what each contains
- Dependency direction between them; any enforcement tool
  (`import-linter`, `dependency-cruiser`, ArchUnit)
- Where business rules live versus I/O
- Existing ADRs in `docs/adr/` or `docs/decisions/`

## 5. Conventions (from the code, not from preference)
- Error handling: exceptions vs result types; where they are converted
- Logging: library, structure, correlation id propagation
- Configuration access: central or scattered
- Naming, file layout, test naming — read the last 20 merged changes

## 6. Landmines
- Tests that must run alone; known-flaky areas
- Generated files that must not be hand-edited
- Long-running or destructive scripts
- Areas with an owner you should ask first

## Record it
Write the findings into the project profile (`context-engineering`). Re-deriving
this every session is waste; a stale entry is a trap — fix on contact.
