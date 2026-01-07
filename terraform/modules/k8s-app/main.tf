resource "kubernetes_config_map" "app_config" {
  metadata {
    name = "${var.app_name}-config"
  }

  data = {
    LANGSMITH_TRACING    = "true"
    MODEL                = var.model_name
    EMBEDDING_MODEL_NAME = var.embedding_model_name
  }
}

resource "kubernetes_secret" "app_secrets" {
  metadata {
    name = "${var.app_name}-secrets"
  }

  data = {
    POSTGRES_DB_URL     = var.database_url
    OPENAI_API_KEY      = var.openai_api_key
    LANGSMITH_API_KEY   = var.langsmith_api_key
    HCAPTCHA_SECRET_KEY = var.hcaptcha_secret_key
  }

  type = "Opaque"
}

resource "kubernetes_deployment" "app" {
  metadata {
    name = var.app_name
    labels = {
      app = var.app_name
    }
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        app = var.app_name
      }
    }

    template {
      metadata {
        labels = {
          app = var.app_name
        }
      }

      spec {
        container {
          image = var.image
          name  = var.app_name

          port {
            container_port = 8000
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 5
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.app_config.metadata[0].name
            }
          }

          env_from {
            secret_ref {
              name = kubernetes_secret.app_secrets.metadata[0].name
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "app" {
  metadata {
    name = var.app_name
  }
  spec {
    selector = {
      app = var.app_name
    }
    port {
      port        = 80
      target_port = 8000
    }
    type = "LoadBalancer"
  }
}

# Job to initialize the database (create tables, install extensions, ingest docs)
resource "kubernetes_job" "db_init" {
  metadata {
    name = "${var.app_name}-db-init"
  }

  spec {
    template {
      metadata {
        name = "${var.app_name}-db-init"
      }
      spec {
        container {
          name    = "db-init"
          image   = var.image
          command = ["python", "init_database.py"]

          env_from {
            config_map_ref {
              name = kubernetes_config_map.app_config.metadata[0].name
            }
          }

          env_from {
            secret_ref {
              name = kubernetes_secret.app_secrets.metadata[0].name
            }
          }
        }
        restart_policy = "OnFailure"
      }
    }
    backoff_limit = 4
    ttl_seconds_after_finished = 300 # Clean up 5 minutes after finishing
  }
  
  # Ensure the job runs after secrets are created
  depends_on = [
    kubernetes_secret.app_secrets,
    kubernetes_config_map.app_config
  ]
}

output "load_balancer_hostname" {
  value = kubernetes_service.app.status.0.load_balancer.0.ingress.0.hostname
}