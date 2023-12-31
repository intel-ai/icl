# https://github.com/minio/operator/tree/master/helm/operator
resource "helm_release" "operator" {
  name = "operator"
  namespace = "minio"
  create_namespace = true
  chart = "https://github.com/minio/operator/raw/v5.0.10/helm-releases/operator-5.0.10.tgz"
  values = [
    <<-EOT
      console:
        ingress:
          enabled: true
          host: "minio.${var.ingress_domain}"
    EOT
  ]
}

resource "kubernetes_ingress_v1" "endpoint" {
  depends_on = [helm_release.operator]
  metadata {
    name = "minio"
    namespace = "minio"
    annotations = {
      "nginx.ingress.kubernetes.io/backend-protocol" = "HTTPS"
      "nginx.ingress.kubernetes.io/proxy-buffering" = "off"
      "nginx.ingress.kubernetes.io/proxy-body-size" = "0"
      "nginx.ingress.kubernetes.io/server-snippet" = <<-EOF
        # To allow special characters in headers
        ignore_invalid_headers off;
      EOF
    }
  }
  spec {
    rule {
      host = "s3.${var.ingress_domain}"
      http {
        path {
          path = "/"
          backend {
            service {
              name = "minio"
              port {
                name = "https-minio"
              }
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_secret" "default_user" {
  depends_on = [helm_release.operator]
  metadata {
    name = "x1miniouser"
    namespace = "minio"
  }
  data = {
    CONSOLE_ACCESS_KEY = "x1miniouser"
    CONSOLE_SECRET_KEY = "x1miniopass"
  }
}

# https://github.com/minio/operator/tree/master/helm/tenant
resource "helm_release" "minio_ha" {
  depends_on = [helm_release.operator, kubernetes_secret.default_user]
  count = var.minio_ha_enabled ? 1 : 0
  name = "minio"
  namespace = "minio"
  create_namespace = true
  chart = "https://github.com/minio/operator/raw/v5.0.10/helm-releases/tenant-5.0.10.tgz"
  values = [
    <<-EOT
      secrets:
        name: minio-env-configuration
      tenant:
        name: minio
        configuration:
          name: minio-env-configuration
        pools:
          - name: pool-0
            servers: ${var.minio_servers}
            # TODO: move to variables
            volumesPerServer: 4
            size: 1.5T
            storageClassName: local-storage
        prometheus:
          storageClassName: "${var.default_storage_class}"
        log:
          db:
            volumeClaimTemplate:
              spec:
                storageClassName: "${var.default_storage_class}"
        buckets:
          - name: prefect
        users:
          - name: x1miniouser
    EOT
  ]
}

# https://github.com/minio/operator/tree/master/helm/tenant
resource "helm_release" "minio" {
  depends_on = [helm_release.operator, kubernetes_secret.default_user]
  count = var.minio_ha_enabled ? 0 : 1
  name = "minio"
  namespace = "minio"
  create_namespace = true
  chart = "https://github.com/minio/operator/raw/v5.0.10/helm-releases/tenant-5.0.10.tgz"
  values = [
    <<-EOT
      secrets:
        name: minio-env-configuration
      tenant:
        name: minio
        configuration:
          name: minio-env-configuration
        pools:
          - name: pool-0
            servers: 1
            volumesPerServer: 1
            size: 10Gi
            storageClassName: "${var.default_storage_class}"
        prometheus: null
        log: null
        buckets:
          - name: prefect
        users:
          - name: x1miniouser
    EOT
  ]
}

