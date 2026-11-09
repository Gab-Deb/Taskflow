terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.6"
    }
  }
}

provider "docker" {}

variable "web_count" {
  description = "Nombre de conteneurs web à créer"
  type        = number
  default     = 2
}

resource "docker_image" "python" {
  name         = "python:3.12-slim"
  keep_locally = true
}

# Chaque conteneur sert /srv/www sur le port 80 ; Ansible y dépose index.html.
resource "docker_container" "web" {
  count   = var.web_count
  name    = "taskflow-web-${count.index + 1}"
  image   = docker_image.python.image_id
  command = ["sh", "-c", "mkdir -p /srv/www && exec python -m http.server 80 --directory /srv/www"]

  ports {
    internal = 80
    external = 8081 + count.index
    ip       = "127.0.0.1"
  }
}

output "urls" {
  value = [for c in docker_container.web : "http://127.0.0.1:${c.ports[0].external}"]
}
