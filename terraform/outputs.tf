output "instance_public_ip" {
  value       = aws_eip.ec2-eip.public_ip
  description = "The public IP address of the ec2 instance"
}

output "ecr_url" {
  value       = aws_ecr_repository.cosmidex-ecr.repository_url
  description = "ECR repo url"
}

output "bucket_name" {
  value       = aws_s3_bucket.cosmidex_bucket.bucket
  description = "Cosmidex s3 bucket name"
}
