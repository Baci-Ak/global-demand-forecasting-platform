# ==============================================================================
# GDF Terraform Orchestration Makefile (dev)
# ==============================================================================
#
# Purpose
# - Run Terraform init/plan/apply/destroy for each prod stack from ONE place.
# - Enforce stack ordering (apply forward, destroy reverse).
# - Keep commands consistent and repeatable for engineers + CI.
#
# Usage
#   make plan-all
#   make apply-all
#   make destroy-all
#
#   make plan-network
#   make apply-mwaa
#   make destroy-monitoring
#
# Notes / Best practices
# - Each stack directory MUST contain:
#     - backend.hcl
#     - terraform.tfvars
# - We always run `terraform init -reconfigure -backend-config=backend.hcl`
#   to ensure the correct remote backend is used.
# - The Makefile uses `terraform -chdir=<stack>` so you can run it from here.
# ==============================================================================

SHELL := /bin/bash

# ==============================================================================
# Terraform CLI
# ==============================================================================
TERRAFORM ?= terraform

# ==============================================================================
# Stack ordering (dependencies)
# ------------------------------------------------------------------------------
# APPLY order matters (dependencies first)
# DESTROY order must be reverse of apply
#
# Keep this list aligned with directories in this folder.
# ==============================================================================
STACKS := iam network ssm-jumphost s3 rds-postgres redshift mwaa monitoring

# ==============================================================================
# Phony targets
# ------------------------------------------------------------------------------
# IMPORTANT:
# Do NOT list explicit plan-<stack> targets here, or they override pattern rules.
# ==============================================================================
.PHONY: \
	help \
	list-stacks \
	plan-all apply-all destroy-all \
	plan-% apply-% destroy-%

# ==============================================================================
# Help
# ==============================================================================
help:
	@echo ""
	@echo "GDF Terraform (prod) - orchestration targets"
	@echo "------------------------------------------------------------"
	@echo "Stacks:"
	@printf "  %s\n" $(STACKS)
	@echo ""
	@echo "All stacks:"
	@echo "  make plan-all"
	@echo "  make apply-all"
	@echo "  make destroy-all"
	@echo ""
	@echo "Single stack:"
	@echo "  make plan-<stack>"
	@echo "  make apply-<stack>"
	@echo "  make destroy-<stack>"
	@echo ""

list-stacks:
	@printf "%s\n" $(STACKS)

# ==============================================================================
# Internal helpers
# ==============================================================================
define assert_stack
case " $(STACKS) " in *" $(1) "*) ;; *) \
  echo "ERROR: unknown stack '$(1)'. Valid stacks: $(STACKS)" >&2; \
  exit 2 ;; \
esac
endef

define tf_init
	$(TERRAFORM) -chdir=$(1) init -reconfigure >/dev/null
endef

define tf_plan
	$(TERRAFORM) -chdir=$(1) plan -var-file=terraform.tfvars
endef

define tf_apply
	$(TERRAFORM) -chdir=$(1) apply -auto-approve -var-file=terraform.tfvars
endef

define tf_destroy
	$(TERRAFORM) -chdir=$(1) destroy -auto-approve -var-file=terraform.tfvars
endef

# ==============================================================================
# Multi-stack targets
# ==============================================================================
plan-all:
	@set -euo pipefail; \
	for s in $(STACKS); do \
		echo "== plan $$s =="; \
		$(call tf_init,$$s); \
		$(call tf_plan,$$s); \
	done

apply-all:
	@set -euo pipefail; \
	for s in $(STACKS); do \
		echo "== apply $$s =="; \
		$(call tf_init,$$s); \
		$(call tf_apply,$$s); \
	done

destroy-all:
	@set -euo pipefail; \
	rev_stacks="$$(echo "$(STACKS)" | awk '{for(i=NF;i>=1;i--) printf $$i" ";}')"; \
	for s in $$rev_stacks; do \
		echo "== destroy $$s =="; \
		$(call tf_init,$$s); \
		$(call tf_destroy,$$s); \
	done

# ==============================================================================
# Single-stack targets
# ==============================================================================
plan-%:
	@set -euo pipefail; \
	$(call assert_stack,$*); \
	echo "== plan $* =="; \
	$(call tf_init,$*); \
	$(call tf_plan,$*)

apply-%:
	@set -euo pipefail; \
	$(call assert_stack,$*); \
	echo "== apply $* =="; \
	$(call tf_init,$*); \
	$(call tf_apply,$*)

destroy-%:
	@set -euo pipefail; \
	$(call assert_stack,$*); \
	echo "== destroy $* =="; \
	$(call tf_init,$*); \
	$(call tf_destroy,$*)