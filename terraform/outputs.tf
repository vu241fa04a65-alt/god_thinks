output "database_endpoint" {
  description = "PostgreSQL Host Endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "database_url" {
  description = "Application DATABASE_URL connection string"
  sensitive   = true
  value       = "postgresql://${aws_db_instance.postgres.username}:${random_password.db_password.result}@${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
}

output "s3_bucket_name" {
  description = "S3 Bucket Name for Leaf Images"
  value       = aws_s3_bucket.leaf_storage.bucket
}

output "s3_bucket_arn" {
  description = "S3 Bucket ARN"
  value       = aws_s3_bucket.leaf_storage.arn
}
