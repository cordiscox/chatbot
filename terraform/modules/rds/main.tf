resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.environment}-db-subnet-group"
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.environment}-rds-sg"
  description = "Allow inbound traffic from EKS"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from EKS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.eks_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-rds-sg"
  }
}

resource "random_password" "password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_db_parameter_group" "main" {
  name   = "${var.environment}-pgvector-pg"
  family = "postgres16"

  parameter {
    name  = "rds.force_ssl"
    value = "0" # Set to 1 to force SSL in production
  }
}

resource "aws_db_instance" "main" {
  identifier        = "${var.environment}-chatbot-db"
  engine            = "postgres"
  engine_version    = "16.3"
  instance_class    = "db.t3.micro" # Free tier eligible
  allocated_storage = 20
  storage_type      = "gp2"

  db_name  = "chatbot_db"
  username = "dbadmin"
  password = random_password.password.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.main.name

  skip_final_snapshot = true # Set to false for production
  publicly_accessible = false
  
  # Ensure extensions like vector can be created
  apply_immediately = true

  tags = {
    Name = "${var.environment}-chatbot-db"
  }
}
