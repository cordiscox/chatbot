output "db_host" {
  value       = aws_db_instance.main.address
  description = "The hostname of the RDS instance"
}

output "db_name" {
  value       = aws_db_instance.main.db_name
  description = "The name of the database"
}

output "db_username" {
  value       = aws_db_instance.main.username
  description = "The username for the database"
}

output "db_password" {
  value       = aws_db_instance.main.password
  description = "The password for the database"
  sensitive   = true
}

output "db_port" {
  value       = aws_db_instance.main.port
  description = "The port of the database"
}
