# ==============================================================================
# CropHealthAI Terraform Stub Configuration
# Provisions Managed PostgreSQL (AWS RDS) and Leaf Image Storage (AWS S3)
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ------------------------------------------------------------------------------
# VPC & Networking for Managed Database
# ------------------------------------------------------------------------------
resource "aws_vpc" "crophealth_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "crophealth-${var.environment}-vpc"
    Environment = var.environment
  }
}

resource "aws_subnet" "db_subnet_a" {
  vpc_id            = aws_vpc.crophealth_vpc.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "crophealth-${var.environment}-db-a"
  }
}

resource "aws_subnet" "db_subnet_b" {
  vpc_id            = aws_vpc.crophealth_vpc.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name = "crophealth-${var.environment}-db-b"
  }
}

resource "aws_db_subnet_group" "db_subnets" {
  name       = "crophealth-${var.environment}-db-subnets"
  subnet_ids = [aws_subnet.db_subnet_a.id, aws_subnet.db_subnet_b.id]

  tags = {
    Name = "CropHealth Database Subnet Group"
  }
}

resource "aws_security_group" "db_sg" {
  name        = "crophealth-${var.environment}-db-sg"
  description = "Allow inbound PostgreSQL traffic from backend application"
  vpc_id      = aws_vpc.crophealth_vpc.id

  ingress {
    description = "PostgreSQL Access"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.crophealth_vpc.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ------------------------------------------------------------------------------
# Managed PostgreSQL (AWS RDS)
# ------------------------------------------------------------------------------
resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "aws_db_instance" "postgres" {
  identifier             = "crophealth-${var.environment}-pg"
  engine                 = "postgres"
  engine_version         = "15.5"
  instance_class         = var.db_instance_class
  allocated_storage      = 20
  max_allocated_storage  = 100
  storage_type           = "gp3"
  db_name                = "crophealth_db"
  username               = "crophealth_admin"
  password               = random_password.db_password.result
  db_subnet_group_name   = aws_db_subnet_group.db_subnets.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  skip_final_snapshot    = true
  deletion_protection    = false

  backup_retention_period = 7
  storage_encrypted       = true

  tags = {
    Name        = "CropHealthAI PostgreSQL"
    Environment = var.environment
  }
}

# ------------------------------------------------------------------------------
# Managed Object Storage (AWS S3) for Leaf Images & Overlays
# ------------------------------------------------------------------------------
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket" "leaf_storage" {
  bucket = "crophealth-${var.environment}-leaf-storage-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "CropHealthAI Leaf Image & Grad-CAM Storage"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "storage_versioning" {
  bucket = aws_s3_bucket.leaf_storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "storage_encryption" {
  bucket = aws_s3_bucket.leaf_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "storage_cors" {
  bucket = aws_s3_bucket.leaf_storage.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}
