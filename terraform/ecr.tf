resource "aws_ecr_repository" "cosmidex-ecr" {
  name                 = "cosmidex-repo"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

}
