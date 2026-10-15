# Keep Git and OCI release tags Docker-safe while supplying uv a PEP 440 version
SKA_MID_PYTHON_VERSION = $(shell \
	. $(RELEASE_SUPPORT); \
	RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; \
	CONFIG=$(CONFIG) setReleaseFile; \
	version=$$(getPythonCompliantVersion); \
	if [[ "$$version" =~ ^([0-9]+\.[0-9]+\.[0-9]+)-dev([0-9]+)-(.*)$$ ]]; then \
		printf '%s.dev%s+%s\n' "$${BASH_REMATCH[1]}" "$${BASH_REMATCH[2]}" "$${BASH_REMATCH[3]//-/.}"; \
	else \
		printf '%s\n' "$$version"; \
	fi)

# Override the submodule's target-specific VERSION for Python package metadata.
python-do-set-release: VERSION := $(SKA_MID_PYTHON_VERSION)