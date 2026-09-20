# ---------------------------------------------------------------------------
# EC2 instance role — lets the running instance call S3 (planet images),
# pull from ECR, and be reachable via SSM (for GitHub Actions deploys).
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "permissions" {
  statement {
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.cosmidex_bucket.arn]
  }

  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.cosmidex_bucket.arn}/*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchCheckLayerAvailability",
    ]
    resources = [aws_ecr_repository.cosmidex-ecr.arn]
  }
}

resource "aws_iam_role" "cosmidex-ec2" {
  name               = "cosmidex-ec2-role"
  path               = "/"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy" "cosmidex-ec2-permissions" {
  name   = "cosmidex-ec2-permissions"
  role   = aws_iam_role.cosmidex-ec2.id
  policy = data.aws_iam_policy_document.permissions.json
}

# AWS-managed policy (not authored here) that lets the SSM Agent on the
# instance register with Systems Manager and receive Run Commands.
resource "aws_iam_role_policy_attachment" "cosmidex-ssm" {
  role       = aws_iam_role.cosmidex-ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "cosmidex-ec2" {
  name = "cosmidex-ec2-profile"
  role = aws_iam_role.cosmidex-ec2.name
}

# ---------------------------------------------------------------------------
# GitHub Actions OIDC role — lets CI push images to ECR and trigger deploys
# via SSM SendCommand, without storing any long-lived AWS credentials.
# ---------------------------------------------------------------------------

resource "aws_iam_openid_connect_provider" "cosmidex" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

data "aws_iam_policy_document" "github" {
  statement {
    effect = "Allow"

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.cosmidex.arn]
    }

    actions = ["sts:AssumeRoleWithWebIdentity"]

    # Only accept tokens issued for AWS's own token service...
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # ...and only when they say they came from this exact repo, any branch.
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:zaccheatle/cosmidex:*"]
    }
  }
}

data "aws_iam_policy_document" "github-permissions" {
  statement {
    effect    = "Allow"
    actions   = ["ssm:SendCommand"]
    resources = [aws_instance.cosmidex.arn]
  }

  statement {
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
    ]
    resources = [aws_ecr_repository.cosmidex-ecr.arn]
  }
}

resource "aws_iam_role" "cosmidex-github" {
  name               = "cosmidex-github-role"
  path               = "/"
  assume_role_policy = data.aws_iam_policy_document.github.json
}

resource "aws_iam_role_policy" "github-permissions" {
  name   = "cosmidex-github-permissions"
  role   = aws_iam_role.cosmidex-github.id
  policy = data.aws_iam_policy_document.github-permissions.json
}
