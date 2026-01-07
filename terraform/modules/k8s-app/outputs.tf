output "service_hostname" {
  value = kubernetes_service.app.status.0.load_balancer.0.ingress.0.hostname
}