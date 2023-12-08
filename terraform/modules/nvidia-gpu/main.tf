# R525 driver is used to support all GPUs including latest L4 available in GKE v1.28
# Instructions found here: (https://cloud.google.com/kubernetes-engine/docs/how-to/gpus#ubuntu)

# TO DO: Assign default driver version variable in gke.sh and allow it to be overridden by user.
data "http" "nvidia_driver_installer_manifest" {
  url = "https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/ubuntu/daemonset-preloaded-R525.yaml"
}

resource "kubernetes_manifest" "nvidia_driver_installer" {
  manifest = yamldecode(data.http.nvidia_driver_installer_manifest.response_body)
}

# Create a namespace for the NVIDIA GPU Operator
resource "kubernetes_namespace" "gpu_operator" {
  metadata {
    name = "gpu-operator"
  }
}

resource "helm_release" "gpu_operator" {
  name       = "gpu-operator"
  repository = "https://helm.ngc.nvidia.com/nvidia"
  chart      = "gpu-operator"
  namespace  = "gpu-operator"
  create_namespace = true

  set {
    name  = "wait"
    value = "true"
  }
  # Additional Settings
}

# Create resource quota for the qpu_operator (OPTIONAL)
#resource "kubernetes_resource_quota" "gpu_operator_quota" {
#  metadata {
#    name      = "gpu-operator-quota"
#    namespace = kubernetes_namespace.gpu_operator.metadata[0].name
#  }
#
#  spec {
#    hard = {
#      "pods" = 100
#    }
#
#    scope_selector {
#      match_expressions {
#        operator  = "In"
#        scope_name = "PriorityClass"
#        values     = ["system-node-critical", "system-cluster-critical"]
#      }
#    }
#  }
#}