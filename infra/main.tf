terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.app_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" { state = "available" }

locals {
  name_prefix        = "${var.app_name}-${var.environment}"
  account_id         = data.aws_caller_identity.current.account_id
  ecr_image_uri      = "${local.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.app_name}:${var.ecr_image_tag}"
  models_bucket_name = "${var.app_name}-models-${local.account_id}"
}
