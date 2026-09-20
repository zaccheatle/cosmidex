provider "aws" {
  region  = var.aws_region
  profile = "zac"

  default_tags {
    tags = {
      Project   = "cosmidex"
      Env       = "prod"
      ManagedBy = "terraform"
    }
  }



}
