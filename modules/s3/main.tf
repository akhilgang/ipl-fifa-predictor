variable "project_name"                 { type=string }
variable "versioning"                   { type=bool }

resource "random_id" "suffix" { byte_length = 4 }
resource "aws_s3_bucket" "this" {
  bucket = "${var.project_name}-model-data--${random_id.suffix.hex}"

  tags = {
    Name = "${var.project_name}-model"
    # Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = var.versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls   = true
  block_public_policy = true
  ignore_public_acls  = true
  restrict_public_buckets = true
}
output "bucket_name" {
  value = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  value = aws_s3_bucket.this.arn
}