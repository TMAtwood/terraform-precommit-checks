#!/usr/bin/env python3
"""
Pre-commit hook to validate Terraform/OpenTofu resource tags.

This hook ensures:
1. Required tags are present on all taggable resources
2. Tag keys match exact case sensitivity
3. Tag values match allowed values (if specified) with exact case
4. Optional tags use correct case sensitivity (if present)

Supports AWS, Azure, GCP, and other providers.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class TerraformTagChecker:
    """Check for proper tag compliance in Terraform/OpenTofu files."""

    # Default taggable resources by provider
    # This is a comprehensive but not exhaustive list
    DEFAULT_TAGGABLE_RESOURCES = {
        "aws": [
            # Compute
            "aws_instance",
            "aws_launch_template",
            "aws_ami",
            "aws_ami_copy",
            "aws_ami_from_instance",
            "aws_ec2_capacity_reservation",
            "aws_ec2_fleet",
            "aws_spot_fleet_request",
            "aws_spot_instance_request",
            # Storage
            "aws_ebs_volume",
            "aws_ebs_snapshot",
            "aws_s3_bucket",
            "aws_s3_bucket_object",
            "aws_s3_object",
            "aws_efs_file_system",
            "aws_fsx_backup",
            "aws_fsx_lustre_file_system",
            "aws_fsx_ontap_file_system",
            "aws_fsx_openzfs_file_system",
            "aws_fsx_windows_file_system",
            # Networking
            "aws_vpc",
            "aws_subnet",
            "aws_internet_gateway",
            "aws_nat_gateway",
            "aws_route_table",
            "aws_security_group",
            "aws_network_interface",
            "aws_eip",
            "aws_vpc_endpoint",
            "aws_vpc_peering_connection",
            "aws_customer_gateway",
            "aws_vpn_gateway",
            "aws_vpn_connection",
            "aws_network_acl",
            "aws_egress_only_internet_gateway",
            "aws_lb",
            "aws_alb",
            "aws_lb_target_group",
            "aws_alb_target_group",
            # Database
            "aws_db_instance",
            "aws_db_cluster",
            "aws_db_snapshot",
            "aws_db_cluster_snapshot",
            "aws_rds_cluster",
            "aws_rds_cluster_instance",
            "aws_elasticache_cluster",
            "aws_elasticache_replication_group",
            "aws_dynamodb_table",
            "aws_neptune_cluster",
            "aws_neptune_cluster_instance",
            "aws_docdb_cluster",
            "aws_docdb_cluster_instance",
            # Container & Orchestration
            "aws_ecs_cluster",
            "aws_ecs_service",
            "aws_ecs_task_definition",
            "aws_eks_cluster",
            "aws_eks_node_group",
            "aws_ecr_repository",
            # Lambda & Serverless
            "aws_lambda_function",
            "aws_lambda_layer_version",
            # IAM
            "aws_iam_role",
            "aws_iam_user",
            "aws_iam_policy",
            "aws_iam_instance_profile",
            "aws_iam_openid_connect_provider",
            "aws_iam_saml_provider",
            # Monitoring & Management
            "aws_cloudwatch_log_group",
            "aws_cloudwatch_metric_alarm",
            "aws_cloudwatch_dashboard",
            "aws_sns_topic",
            "aws_sqs_queue",
            # Security
            "aws_kms_key",
            "aws_kms_alias",
            "aws_secretsmanager_secret",
            "aws_acm_certificate",
            "aws_wafv2_web_acl",
            "aws_wafv2_ip_set",
            "aws_wafv2_regex_pattern_set",
            # Application Services
            "aws_api_gateway_rest_api",
            "aws_apigatewayv2_api",
            "aws_cloudfront_distribution",
            "aws_route53_zone",
            "aws_route53_health_check",
            # Analytics & ML
            "aws_kinesis_stream",
            "aws_kinesis_firehose_delivery_stream",
            "aws_elasticsearch_domain",
            "aws_opensearch_domain",
            "aws_glue_job",
            "aws_glue_crawler",
            "aws_sagemaker_notebook_instance",
            "aws_sagemaker_model",
            # Backup & DR
            "aws_backup_plan",
            "aws_backup_vault",
        ],
        "azurerm": [
            # Compute
            "azurerm_virtual_machine",
            "azurerm_linux_virtual_machine",
            "azurerm_windows_virtual_machine",
            "azurerm_virtual_machine_scale_set",
            "azurerm_linux_virtual_machine_scale_set",
            "azurerm_windows_virtual_machine_scale_set",
            "azurerm_image",
            "azurerm_snapshot",
            # Storage
            "azurerm_storage_account",
            "azurerm_storage_container",
            "azurerm_storage_blob",
            "azurerm_managed_disk",
            # Networking
            "azurerm_virtual_network",
            "azurerm_subnet",
            "azurerm_network_interface",
            "azurerm_network_security_group",
            "azurerm_public_ip",
            "azurerm_lb",
            "azurerm_application_gateway",
            "azurerm_vpn_gateway",
            "azurerm_virtual_network_gateway",
            "azurerm_express_route_circuit",
            # Database
            "azurerm_sql_server",
            "azurerm_sql_database",
            "azurerm_postgresql_server",
            "azurerm_postgresql_flexible_server",
            "azurerm_mysql_server",
            "azurerm_mysql_flexible_server",
            "azurerm_mariadb_server",
            "azurerm_cosmosdb_account",
            "azurerm_redis_cache",
            # Container & Orchestration
            "azurerm_kubernetes_cluster",
            "azurerm_container_registry",
            "azurerm_container_group",
            # App Services
            "azurerm_app_service",
            "azurerm_linux_web_app",
            "azurerm_windows_web_app",
            "azurerm_function_app",
            "azurerm_linux_function_app",
            "azurerm_windows_function_app",
            # Resource Management
            "azurerm_resource_group",
            # Monitoring
            "azurerm_log_analytics_workspace",
            "azurerm_application_insights",
            # Security
            "azurerm_key_vault",
            "azurerm_key_vault_key",
            "azurerm_key_vault_secret",
        ],
        "google": [
            # Compute (GCP uses labels instead of tags)
            "google_compute_instance",
            "google_compute_disk",
            "google_compute_image",
            "google_compute_snapshot",
            "google_compute_instance_template",
            "google_compute_instance_group",
            "google_compute_instance_group_manager",
            # Networking
            "google_compute_network",
            "google_compute_subnetwork",
            "google_compute_address",
            "google_compute_global_address",
            "google_compute_firewall",
            "google_compute_router",
            "google_compute_vpn_gateway",
            "google_compute_forwarding_rule",
            "google_compute_global_forwarding_rule",
            "google_compute_backend_service",
            "google_compute_health_check",
            # Storage
            "google_storage_bucket",
            "google_storage_bucket_object",
            "google_filestore_instance",
            # Database
            "google_sql_database_instance",
            "google_bigtable_instance",
            "google_spanner_instance",
            "google_firestore_database",
            # Container & Orchestration
            "google_container_cluster",
            "google_container_node_pool",
            "google_artifact_registry_repository",
            # Serverless
            "google_cloudfunctions_function",
            "google_cloud_run_service",
            # Monitoring
            "google_logging_log_sink",
            "google_monitoring_alert_policy",
            # Security
            "google_kms_key_ring",
            "google_kms_crypto_key",
            "google_secret_manager_secret",
            # Pub/Sub
            "google_pubsub_topic",
            "google_pubsub_subscription",
        ],
        "oci": [
            # Compute
            "oci_core_instance",
            "oci_core_boot_volume",
            "oci_core_volume",
            "oci_core_image",
            # Networking
            "oci_core_vcn",
            "oci_core_subnet",
            "oci_core_security_list",
            "oci_core_network_security_group",
            "oci_core_internet_gateway",
            "oci_core_nat_gateway",
            "oci_core_service_gateway",
            "oci_core_local_peering_gateway",
            "oci_core_drg",
            # Storage
            "oci_objectstorage_bucket",
            "oci_file_storage_file_system",
            # Database
            "oci_database_db_system",
            "oci_database_autonomous_database",
            # Container
            "oci_containerengine_cluster",
            "oci_containerengine_node_pool",
        ],
    }

    # Pattern to detect resource blocks
    RESOURCE_BLOCK_PATTERN = re.compile(r'^\s*resource\s+"([^"]+)"\s+"([^"]+)"\s*\{', re.MULTILINE)

    def __init__(
        self,
        files: List[str],
        config_file: Optional[str] = None,
        required_tags: Optional[List[Dict[str, Any]]] = None,
        optional_tags: Optional[List[Dict[str, str]]] = None,
        taggable_resources: Optional[Dict[str, List[str]]] = None,
    ):
        """
        Initialize the tag checker.

        Args:
            files: List of files to check
            config_file: Path to .terraform-tags.yaml config file
            required_tags: List of required tag definitions (from args)
            optional_tags: List of optional tag definitions (from args)
            taggable_resources: Custom taggable resources dict (from config)
        """
        self.files = files
        self.errors: List[Tuple[str, int, str, str]] = []  # file, line, resource, msg
        self.config_file = config_file

        # Load configuration
        self.config = self._load_config(
            config_file, required_tags, optional_tags, taggable_resources
        )

        # Extract configuration
        self.required_tags: List[Dict[str, Any]] = self.config.get("required_tags", [])
        self.optional_tags: List[Dict[str, str]] = self.config.get("optional_tags", [])
        self.taggable_resources: Dict[str, List[str]] = self.config.get(
            "taggable_resources", self.DEFAULT_TAGGABLE_RESOURCES
        )

        # Build tag name sets for quick lookup
        self.required_tag_names: Set[str] = {tag["name"] for tag in self.required_tags}
        self.optional_tag_names: Set[str] = {tag["name"] for tag in self.optional_tags}
        self.all_valid_tag_names: Set[str] = self.required_tag_names | self.optional_tag_names

    def _load_config(
        self,
        config_file: Optional[str],
        required_tags: Optional[List[Dict[str, Any]]],
        optional_tags: Optional[List[Dict[str, str]]],
        taggable_resources: Optional[Dict[str, List[str]]],
    ) -> Dict[str, Any]:
        """
        Load configuration from file or arguments.

        Priority: args > config_file > defaults
        """
        config: Dict[str, Any] = {
            "required_tags": [],
            "optional_tags": [],
            "taggable_resources": self.DEFAULT_TAGGABLE_RESOURCES,
        }

        # Load from config file if provided
        if config_file:
            config_path = Path(config_file)
            if config_path.exists():
                try:
                    import yaml

                    with open(config_path, encoding="utf-8") as f:
                        file_config = yaml.safe_load(f) or {}
                        config.update(file_config)
                except ImportError:
                    print(
                        "⚠️  Warning: PyYAML not installed. Using JSON format or args only.",
                        file=sys.stderr,
                    )
                    # Try JSON format as fallback
                    try:
                        with open(config_path, encoding="utf-8") as f:
                            file_config = json.load(f)
                            config.update(file_config)
                    except json.JSONDecodeError as e:
                        print(
                            f"❌ Error: Could not parse config file as JSON: {e}",
                            file=sys.stderr,
                        )
                        sys.exit(1)
            else:
                print(f"⚠️  Warning: Config file not found: {config_file}", file=sys.stderr)

        # Override with args if provided
        if required_tags is not None:
            config["required_tags"] = required_tags
        if optional_tags is not None:
            config["optional_tags"] = optional_tags
        if taggable_resources is not None:
            config["taggable_resources"] = taggable_resources

        return config

    def is_taggable_resource(self, resource_type: str) -> bool:
        """Check if a resource type supports tags/labels."""
        for provider_resources in self.taggable_resources.values():
            if resource_type in provider_resources:
                return True
        return False

    def get_tag_attribute_name(self, resource_type: str) -> str:
        """
        Get the tag attribute name for a resource type.

        AWS/Azure use 'tags', GCP uses 'labels'
        """
        if resource_type.startswith("google_"):
            return "labels"
        return "tags"

    def extract_tags_from_resource(
        self, content: str, resource_start: int, resource_type: str
    ) -> Tuple[Optional[Dict[str, str]], Optional[int]]:
        """
        Extract tags/labels from a resource block.

        Returns:
            Tuple of (tags_dict, line_number) or (None, None) if no tags found
        """
        tag_attr = self.get_tag_attribute_name(resource_type)

        # Find the resource block end
        brace_count = 0
        in_resource = False
        resource_end = resource_start

        for i, char in enumerate(content[resource_start:], start=resource_start):
            if char == "{":
                brace_count += 1
                in_resource = True
            elif char == "}":
                brace_count -= 1
                if in_resource and brace_count == 0:
                    resource_end = i
                    break

        resource_content = content[resource_start:resource_end]

        # Pattern for dynamic tags: tags = merge(...) or similar - we can't validate these
        tags_dynamic_pattern = re.compile(rf"{tag_attr}\s*=\s*(merge|var\.|local\.)")

        # Check for dynamic tags first
        if tags_dynamic_pattern.search(resource_content):
            # Can't validate dynamic tags
            return None, None

        # Find tags/labels block start
        tags_start_pattern = re.compile(rf"{tag_attr}\s*=\s*\{{")
        tags_start_match = tags_start_pattern.search(resource_content)

        if not tags_start_match:
            # No tags found
            tag_line = content[:resource_start].count("\n") + 1
            return {}, tag_line

        # Find the matching closing brace using brace counting
        tags_block_start = tags_start_match.end() - 1  # Position of opening {
        brace_count = 0
        tags_block_end = tags_block_start

        for i, char in enumerate(resource_content[tags_block_start:], start=tags_block_start):
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    tags_block_end = i
                    break

        # Extract content between braces
        tags_content = resource_content[tags_block_start + 1 : tags_block_end]
        tag_line = content[: resource_start + tags_start_match.start()].count("\n") + 1

        # Parse tag key-value pairs
        # Pattern: "key" = "value" or key = "value"
        tag_pattern = re.compile(r'(?:"([^"]+)"|(\w+))\s*=\s*"([^"]*)"')
        tags = {}
        for match in tag_pattern.finditer(tags_content):
            key = match.group(1) or match.group(2)
            value = match.group(3)
            tags[key] = value

        return tags, tag_line

    def validate_required_tags(
        self,
        resource_type: str,
        resource_name: str,
        tags: Dict[str, str],
        file_path: str,
        line_num: int,
    ) -> None:
        """Validate that all required tags are present with correct case and values."""
        for required_tag in self.required_tags:
            tag_name = required_tag["name"]
            allowed_values = required_tag.get("allowed_values")
            pattern = required_tag.get("pattern")

            # Check if tag exists (case-sensitive)
            if tag_name not in tags:
                # Check for case mismatch
                tag_name_lower = tag_name.lower()
                found_mismatch = None
                for existing_tag in tags:
                    if existing_tag.lower() == tag_name_lower:
                        found_mismatch = existing_tag
                        break

                if found_mismatch:
                    error_msg = (
                        f"Required tag '{tag_name}' has incorrect case. "
                        f"Found '{found_mismatch}' but expected '{tag_name}'."
                    )
                else:
                    error_msg = f"Required tag '{tag_name}' is missing."

                self.errors.append(
                    (file_path, line_num, f"{resource_type}.{resource_name}", error_msg)
                )
                continue

            # Validate tag value
            tag_value = tags[tag_name]

            # Check for empty value
            if not tag_value or tag_value.strip() == "":
                error_msg = f"Required tag '{tag_name}' has an empty value."
                self.errors.append(
                    (file_path, line_num, f"{resource_type}.{resource_name}", error_msg)
                )
                continue

            # Check allowed values if specified
            if allowed_values:
                if tag_value not in allowed_values:
                    # Check for case mismatch
                    value_lower = tag_value.lower()
                    found_mismatch = None
                    for allowed_value in allowed_values:
                        if allowed_value.lower() == value_lower:
                            found_mismatch = allowed_value
                            break

                    if found_mismatch:
                        error_msg = (
                            f"Tag '{tag_name}' value '{tag_value}' has incorrect case. "
                            f"Expected '{found_mismatch}' (allowed: {allowed_values})."
                        )
                    else:
                        error_msg = (
                            f"Tag '{tag_name}' has invalid value '{tag_value}'. "
                            f"Allowed values: {allowed_values}."
                        )

                    self.errors.append(
                        (
                            file_path,
                            line_num,
                            f"{resource_type}.{resource_name}",
                            error_msg,
                        )
                    )
            # Check pattern if specified (and no allowed_values)
            elif pattern:
                try:
                    pattern_regex = re.compile(pattern)
                    if not pattern_regex.match(tag_value):
                        pattern_str = f"Tag '{tag_name}' value '{tag_value}' does not match"
                        error_msg = f"{pattern_str} required pattern '{pattern}'."
                        self.errors.append(
                            (
                                file_path,
                                line_num,
                                f"{resource_type}.{resource_name}",
                                error_msg,
                            )
                        )
                except re.error as e:
                    error_msg = f"Tag '{tag_name}' has invalid regex pattern '{pattern}': {e}"
                    self.errors.append(
                        (
                            file_path,
                            line_num,
                            f"{resource_type}.{resource_name}",
                            error_msg,
                        )
                    )

    def validate_optional_tags(
        self,
        resource_type: str,
        resource_name: str,
        tags: Dict[str, str],
        file_path: str,
        line_num: int,
    ) -> None:
        """Validate optional tags for case sensitivity (if present)."""
        for optional_tag in self.optional_tags:
            tag_name = optional_tag["name"]

            # Optional tags don't need to be present, but if they are,
            # check the case
            if tag_name in tags:
                # Tag is present with correct case, nothing to check
                continue

            # Check if there's a case mismatch
            tag_name_lower = tag_name.lower()
            for existing_tag in tags:
                if existing_tag.lower() == tag_name_lower and existing_tag != tag_name:
                    error_msg = (
                        f"Optional tag '{tag_name}' has incorrect case. "
                        f"Found '{existing_tag}' but expected '{tag_name}'."
                    )
                    self.errors.append(
                        (
                            file_path,
                            line_num,
                            f"{resource_type}.{resource_name}",
                            error_msg,
                        )
                    )
                    break

    def check_file(self, file_path: str) -> bool:
        """
        Check a single file for tag compliance.

        Returns:
            True if file passes checks, False if errors found
        """
        path = Path(file_path)

        # Only check .tf files
        if path.suffix != ".tf":
            return True

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            return False

        # Find all resource blocks
        resource_matches = list(self.RESOURCE_BLOCK_PATTERN.finditer(content))

        if not resource_matches:
            return True

        for match in resource_matches:
            resource_type = match.group(1)
            resource_name = match.group(2)

            # Check if this resource type is taggable
            if not self.is_taggable_resource(resource_type):
                continue

            # Find the line number
            line_num = content[: match.start()].count("\n") + 1

            # Extract tags from the resource
            tags, tag_line = self.extract_tags_from_resource(content, match.start(), resource_type)

            # Skip if tags are dynamic (merge, var, local, etc.)
            if tags is None:
                continue

            # Use tag_line if available, otherwise use resource line
            actual_line = tag_line if tag_line else line_num

            # Validate required tags
            self.validate_required_tags(resource_type, resource_name, tags, file_path, actual_line)

            # Validate optional tags (if present)
            self.validate_optional_tags(resource_type, resource_name, tags, file_path, actual_line)

        return len(self.errors) == 0

    def check_all_files(self) -> bool:
        """
        Check all files provided to the checker.

        Returns:
            True if all files pass, False otherwise
        """
        all_passed = True

        for file_path in self.files:
            if not self.check_file(file_path):
                all_passed = False

        return all_passed

    def print_errors(self) -> None:
        """Print all errors found during checking."""
        if not self.errors:
            return

        print("\n" + "=" * 80, file=sys.stderr)
        print("❌ TERRAFORM TAG VALIDATION FAILED", file=sys.stderr)
        print("=" * 80, file=sys.stderr)

        for file_path, line_num, resource, error_msg in self.errors:
            print(f"\n📁 File: {file_path}", file=sys.stderr)
            print(f"📍 Line: {line_num}", file=sys.stderr)
            print(f"🏷️  Resource: {resource}", file=sys.stderr)
            print(f"⚠️  {error_msg}", file=sys.stderr)

        print("\n" + "=" * 80, file=sys.stderr)
        print("💡 TAG REQUIREMENTS:", file=sys.stderr)
        print("=" * 80, file=sys.stderr)

        if self.required_tags:
            print("\nRequired tags:", file=sys.stderr)
            for tag in self.required_tags:
                tag_name = tag["name"]
                allowed_values = tag.get("allowed_values")
                pattern = tag.get("pattern")

                if allowed_values:
                    print(f"  • {tag_name} (allowed: {allowed_values})", file=sys.stderr)
                elif pattern:
                    print(f"  • {tag_name} (pattern: {pattern})", file=sys.stderr)
                else:
                    print(f"  • {tag_name} (any non-empty value)", file=sys.stderr)

        if self.optional_tags:
            print("\nOptional tags (case-sensitive if used):", file=sys.stderr)
            for tag in self.optional_tags:
                print(f"  • {tag['name']}", file=sys.stderr)

        print("\n" + "=" * 80 + "\n", file=sys.stderr)


def parse_tag_list_arg(arg: str) -> List[Dict[str, Any]]:
    """
    Parse a tag list argument in JSON format.

    Example: '[{"name":"Environment","allowed_values":["Dev","Prod"]},{"name":"Owner"}]'
    """
    try:
        result: List[Dict[str, Any]] = json.loads(arg)
        return result
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing tag list: {e}", file=sys.stderr)
        print("Expected JSON format, e.g.:", file=sys.stderr)
        print(
            '  [{"name":"Environment","allowed_values":["Dev","Prod"]},{"name":"Owner"}]',
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> int:
    """Main entry point for the pre-commit hook."""
    parser = argparse.ArgumentParser(
        description="Validate Terraform/OpenTofu resource tags",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using config file
  check-terraform-tags --config .terraform-tags.yaml main.tf

  # Using command-line args (JSON format)
  check-terraform-tags --required-tags \
    '[{"name":"Environment","allowed_values":["Dev","Staging","Prod"]},{"name":"Owner"}]' main.tf

  # Mixing config file and args (args take precedence)
  check-terraform-tags --config .terraform-tags.yaml --optional-tags '[{"name":"Project"}]' main.tf
""",
    )

    parser.add_argument("files", nargs="*", help="Terraform files to check")
    parser.add_argument(
        "--config",
        dest="config_file",
        help="Path to .terraform-tags.yaml or .terraform-tags.json config file",
    )
    parser.add_argument(
        "--required-tags",
        type=parse_tag_list_arg,
        help='Required tags as JSON list, e.g. [{"name":"Env","allowed_values":["Dev","Prod"]}]',
    )
    parser.add_argument(
        "--optional-tags",
        type=parse_tag_list_arg,
        help='Optional tags as JSON list, e.g. [{"name":"Project"},{"name":"Description"}]',
    )

    args = parser.parse_args()

    if not args.files:
        print("No files to check", file=sys.stderr)
        return 0

    checker = TerraformTagChecker(
        files=args.files,
        config_file=args.config_file,
        required_tags=args.required_tags,
        optional_tags=args.optional_tags,
    )

    if checker.check_all_files():
        print("✅ All taggable resources have valid tags", file=sys.stderr)
        return 0
    else:
        checker.print_errors()
        return 1


if __name__ == "__main__":
    sys.exit(main())
