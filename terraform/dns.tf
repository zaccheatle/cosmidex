resource "aws_eip" "ec2-eip" {
  instance = aws_instance.cosmidex.id
}

data "aws_route53_zone" "cosmidex-domain" {
  name = "cosmidex.com"
}

resource "aws_route53_record" "cosmidex" {
  name    = "cosmidex.com"
  type    = "A"
  zone_id = data.aws_route53_zone.cosmidex-domain.zone_id
  ttl     = 300
  records = [aws_eip.ec2-eip.public_ip]
}
