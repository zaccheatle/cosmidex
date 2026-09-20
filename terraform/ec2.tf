data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}


resource "aws_instance" "cosmidex" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.cosmidex-ec2-sg.id]
  subnet_id              = data.aws_subnets.default.ids[0]
  key_name               = var.key_pair_name
  iam_instance_profile   = aws_iam_instance_profile.cosmidex-ec2.name


  tags = {
    Name = "cosmidex-instance"
  }
}
