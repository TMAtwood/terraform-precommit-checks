# Terraform/OpenTofu Provider Configuration Checker

## 🎯 What This Does

Prevents old-style provider configurations that block `for_each` and `depends_on` at the module level.

## 🌐 Provider Support

**Works with ALL providers:**
- ✅ AWS, Azure, Google Cloud, Oracle Cloud
- ✅ VMware, Kubernetes, Helm, Docker
- ✅ Datadog, PagerDuty, Cloudflare
- ✅ 3,000+ providers in Terraform Registry

## 📚 Documentation

### Start Here
- **[README.md](README.md)** - Complete installation and usage guide
- **[PACKAGE_SUMMARY.md](PACKAGE_SUMMARY.md)** - Quick overview of what's included

### Learn More
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Pattern comparison and examples
- **[MULTI_CLOUD_SUPPORT.md](MULTI_CLOUD_SUPPORT.md)** - Multi-cloud patterns and use cases

## 🚀 Quick Start

```bash
# 1. Install pre-commit
pip install pre-commit

# 2. Copy files to your repo
cp check_provider_config.py /path/to/your/repo/
cp pre-commit-config.yaml /path/to/your/repo/.pre-commit-config.yaml

# 3. Install hook
cd /path/to/your/repo
pre-commit install

# 4. Test
pre-commit run check-provider-config --all-files
```

Or use the automated setup:
```bash
./setup.sh
```

## 📁 Files Overview

### Core Files (Required)
- `check_provider_config.py` - The pre-commit hook
- `pre-commit-config.yaml` - Configuration (rename to `.pre-commit-config.yaml`)

### Setup & Testing
- `setup.sh` - Automated installation script
- `verify_multi_cloud.sh` - Proves provider-agnostic functionality
- `test_hook.py` - Test suite

### Documentation
- `README.md` - Main documentation
- `PACKAGE_SUMMARY.md` - Package overview
- `QUICK_REFERENCE.md` - Quick patterns guide
- `MULTI_CLOUD_SUPPORT.md` - Multi-cloud guide

### Examples - Wrong Pattern (OLD)
- `test_old_style.tf` - AWS old-style
- `test_azure_old.tf` - Azure old-style
- `test_gcp_old.tf` - GCP old-style
- `test_oci_old.tf` - Oracle Cloud old-style

### Examples - Correct Pattern (NEW)
- `test_new_style.tf` - Simple correct example
- `example_multi_provider.tf` - Multi-provider module
- `example_root_module.tf` - Root module with for_each/depends_on
- `example_multi_cloud_module.tf` - Complete multi-cloud module
- `example_multi_cloud_root.tf` - Multi-cloud root with advanced patterns

## ✅ Verification

Run the verification script to prove it works with multiple providers:

```bash
./verify_multi_cloud.sh
```

Output will show detection working for:
- AWS (aws)
- Azure (azurerm)
- Google Cloud (google)
- Oracle Cloud (oci)

## 🎯 What Gets Detected

### Will Fail ❌
```hcl
# Works with ANY provider name
provider "aws" { ... }
provider "azurerm" { ... }
provider "google" { ... }
provider "oci" { ... }
# ... any provider
```

### Will Pass ✅
```hcl
terraform {
  required_providers {
    <provider> = {
      source                = "<source>"
      version               = "<version>"
      configuration_aliases = [<provider>.main]
    }
  }
}
```

## 💡 Why This Matters

**Before:** ❌ Can't use `for_each` or `depends_on` on modules
```hcl
module "example" {
  source   = "./modules/app"
  for_each = var.instances  # ERROR!
}
```

**After:** ✅ Full module meta-argument support
```hcl
module "example" {
  source   = "./modules/app"
  for_each = var.instances  # Works!
  depends_on = [aws_iam_role.app]  # Works!

  providers = {
    aws.main = aws.us_east_1
  }
}
```

## 🔧 Integration

### Git (Automatic)
Runs automatically on every `git commit`

### CI/CD
```bash
pre-commit run check-provider-config --all-files
```

### Manual
```bash
python check_provider_config.py path/to/*.tf
```

## 📊 Use Cases

1. **Multi-region deployment** - Deploy to multiple AWS regions with one module
2. **Multi-cloud** - Combine AWS, Azure, GCP in one infrastructure
3. **Dynamic scaling** - Create N instances of a module
4. **Complex dependencies** - Control module execution order
5. **Better organization** - Reusable modules with flexible configuration

## 🏢 Perfect For

- Platform engineering teams (like yours!)
- Multi-cloud organizations
- Large-scale infrastructure projects
- Enforcing best practices
- Migration from old patterns

## 📝 License

Use freely in your projects. No attribution required.

## 🔗 References

- [Terraform Module Providers](https://developer.hashicorp.com/terraform/language/modules/develop/providers)
- [Module Meta-Arguments](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)
- [OpenTofu Documentation](https://opentofu.org/docs/)

---

**Questions? Check the documentation files above or run `./verify_multi_cloud.sh` to see it in action!**
