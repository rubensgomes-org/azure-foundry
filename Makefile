# Root Makefile — release automation.
# -----------------------------------------------------------------------------
# Ported from the `azure-iac` repo. `VERSION` is the source of truth: the git
# tag is `v$(VERSION)` and the CHANGELOG heading is `[$(VERSION)]`.
#
# The bump targets stop at a LOCAL commit and annotated tag; `release-push` is
# the separate step that publishes. Undo an unpushed bump with
# `git tag -d v<ver> && git reset --hard HEAD~1`.
#
# Portability: runs on macOS (BSD tools) and ubuntu. No `sed -i`; the
# changelog is rewritten through awk into a temp file. Each awk program stays
# on one physical line, since a `\` continuation would land inside its quotes.
#
# Shared bodies live in `define` variables, not $(MAKE) sub-targets, so
# `make -n release-patch` stays an honest dry run.
#
# This project's source code and documentation were generated with the
# assistance of Artificial Intelligence (AI). For more information, please
# refer to the `AI_DISCLAIMER.md` document located in the project's root
# directory.
# -----------------------------------------------------------------------------

# Read once at parse time; recipes that rewrite VERSION re-read it in-shell.
VERSION     := $(shell cat VERSION 2>/dev/null)
RELEASE_TAG := v$(VERSION)

.DEFAULT_GOAL := help

# Read-only preflight: valid VERSION, clean tree, on main, in sync with origin.
# A fetch failure only warns, so the targets still work offline.
define RELEASE_PRECHECK
echo "=== RELEASE PRECHECK ==="; \
if [ ! -f VERSION ]; then \
  echo "ERROR: VERSION file is missing at the repo root." >&2; exit 1; \
fi; \
_v=$$(cat VERSION); \
case "$$_v" in \
  [0-9]*.[0-9]*.[0-9]*) ;; \
  *) echo "ERROR: VERSION '$$_v' is not MAJOR.MINOR.PATCH." >&2; exit 1;; \
esac; \
case "$$_v" in \
  *[!0-9.]*|*.*.*.*|*..*|.*|*.) \
    echo "ERROR: VERSION '$$_v' is not MAJOR.MINOR.PATCH." >&2; exit 1;; \
esac; \
if ! git diff --quiet || ! git diff --cached --quiet; then \
  echo "ERROR: working tree is dirty. Commit or stash before releasing." >&2; \
  git status --short >&2; \
  exit 1; \
fi; \
_br=$$(git rev-parse --abbrev-ref HEAD); \
if [ "$$_br" != "main" ]; then \
  echo "ERROR: releases are cut from main, not '$$_br'." >&2; \
  exit 1; \
fi; \
if git fetch --quiet origin main 2>/dev/null; then \
  if ! git merge-base --is-ancestor FETCH_HEAD HEAD; then \
    echo "ERROR: HEAD does not contain origin/main. Pull main first." >&2; \
    exit 1; \
  fi; \
else \
  echo "  WARN: could not fetch origin, skipping the sync check"; \
fi; \
echo "  ok: VERSION=$$_v, branch=$$_br, tree clean"
endef

# Refuses a release with no `- ` bullets under [Unreleased].
define RELEASE_REQUIRE_UNRELEASED
_n=$$(awk '/^## \[Unreleased\]/{f=1;next} f && /^## \[[0-9]/{exit} f && /^- /{c++} END{print c+0}' CHANGELOG.md); \
if [ "$$_n" -eq 0 ]; then \
  echo "ERROR: CHANGELOG.md [Unreleased] has no entries - nothing to release." >&2; \
  exit 1; \
fi; \
echo "  ok: $$_n changelog entrie(s) under [Unreleased]"
endef

# Tags whatever VERSION currently holds (re-read after RELEASE_BUMP).
define RELEASE_TAG_BODY
_v=$$(cat VERSION); \
_tag="v$$_v"; \
if git rev-parse -q --verify "refs/tags/$$_tag" >/dev/null; then \
  echo "ERROR: tag $$_tag already exists." >&2; exit 1; \
fi; \
git tag -a "$$_tag" -m "Release $$_tag"; \
echo "=== TAGGED $$_tag ==="; \
echo "  nothing has been pushed. Inspect with 'git show --stat HEAD', then:"; \
echo "    make release-push     push main + $$_tag (this publishes the release)"; \
echo "  or undo with:"; \
echo "    git tag -d $$_tag && git reset --hard HEAD~1"
endef

# LEVEL (patch|minor|major) comes from the caller. Every check runs before the
# first write. The roll inserts a fresh [Unreleased] block above the new
# version heading, so the old [Unreleased] body becomes the release notes.
define RELEASE_BUMP
$(RELEASE_PRECHECK); \
$(RELEASE_REQUIRE_UNRELEASED); \
IFS=. read -r _ma _mi _pa < VERSION; \
case "$$LEVEL" in \
  major) _ma=$$((_ma + 1)); _mi=0; _pa=0;; \
  minor) _mi=$$((_mi + 1)); _pa=0;; \
  patch) _pa=$$((_pa + 1));; \
  *) echo "ERROR: unknown bump level '$$LEVEL'." >&2; exit 1;; \
esac; \
_new="$$_ma.$$_mi.$$_pa"; \
if git rev-parse -q --verify "refs/tags/v$$_new" >/dev/null; then \
  echo "ERROR: tag v$$_new already exists." >&2; exit 1; \
fi; \
echo "=== RELEASE $$LEVEL: $$(cat VERSION) -> $$_new ==="; \
printf '%s\n' "$$_new" > VERSION; \
awk -v ver="$$_new" -v day="$$(date +%F)" 'BEGIN{d=0} /^## \[Unreleased\]/ && !d {print; print ""; print "### Added"; print ""; print "### Changed"; print ""; print "### Fixed"; print ""; print "### Removed"; print ""; print "## [" ver "] - " day; d=1; next} {print}' CHANGELOG.md > CHANGELOG.md.tmp; \
mv CHANGELOG.md.tmp CHANGELOG.md; \
git add VERSION CHANGELOG.md; \
git commit -q -m "release: v$$_new"; \
$(RELEASE_TAG_BODY)
endef

.PHONY: version
version:
	@echo "VERSION file : $(VERSION)"
	@echo "Release tag  : $(RELEASE_TAG)"
	@echo "Latest tag   : $$(git describe --tags --abbrev=0 2>/dev/null || echo '(none yet)')"

.PHONY: release-check
release-check:
	@$(RELEASE_PRECHECK); \
	 $(RELEASE_REQUIRE_UNRELEASED); \
	 IFS=. read -r _ma _mi _pa < VERSION; \
	 echo ""; \
	 echo "  current        v$$_ma.$$_mi.$$_pa"; \
	 echo "  release-patch  v$$_ma.$$_mi.$$((_pa + 1))   in-place tweaks, docs, no resource churn"; \
	 echo "  release-minor  v$$_ma.$$((_mi + 1)).0   new resources or workflows"; \
	 echo "  release-major  v$$((_ma + 1)).0.0   destroys/recreates or renames existing resources"

.PHONY: release-patch
release-patch:
	@LEVEL=patch; $(RELEASE_BUMP)

.PHONY: release-minor
release-minor:
	@LEVEL=minor; $(RELEASE_BUMP)

.PHONY: release-major
release-major:
	@LEVEL=major; $(RELEASE_BUMP)

# Escape hatch: re-tags the current VERSION when a bump committed but its tag
# was lost before the push. Requires an existing [VERSION] changelog section.
.PHONY: release-tag
release-tag:
	@$(RELEASE_PRECHECK); \
	 _v=$$(cat VERSION); \
	 if ! grep -q "^## \[$$_v\]" CHANGELOG.md; then \
	   echo "ERROR: CHANGELOG.md has no [$$_v] section. Add one, or use release-<level>." >&2; \
	   exit 1; \
	 fi; \
	 $(RELEASE_TAG_BODY)

# Not undoable. main goes first so the tag never names an unpushed commit; the
# tag push fires release.yml, which publishes the GitHub Release.
.PHONY: release-push
release-push:
	@_tag="$(RELEASE_TAG)"; \
	 if ! git rev-parse -q --verify "refs/tags/$$_tag" >/dev/null; then \
	   echo "ERROR: no local tag $$_tag. Run 'make release-<level>' first." >&2; exit 1; \
	 fi; \
	 echo "=== PUSH $$_tag ==="; \
	 git push origin main; \
	 git push origin "$$_tag"; \
	 echo "  pushed. release.yml is now publishing $$_tag:"; \
	 echo "    gh run list --workflow=release.yml"

.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Release:"
	@echo "  version           Show VERSION, the derived tag, and the latest git tag"
	@echo "  release-check     Preflight only. Reports what each bump would produce"
	@echo "  release-patch     Bump PATCH, roll changelog, commit, tag. Local only"
	@echo "  release-minor     Bump MINOR, roll changelog, commit, tag. Local only"
	@echo "  release-major     Bump MAJOR, roll changelog, commit, tag. Local only"
	@echo "  release-tag       Tag the current VERSION without bumping (escape hatch)"
	@echo "  release-push      Push main + the tag. Not undoable. The tag push"
	@echo "                    fires release.yml, which publishes the Release"
	@echo "  help              This message"
