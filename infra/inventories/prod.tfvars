app_name    = "lstm-stock-api"
environment = "prod"

# Compute
fargate_cpu    = 512 # 0.5 vCPU
fargate_memory = 1024 # 1GB
desired_count  = 1

# Network
container_port      = 8000
vpc_cidr            = "10.0.0.0/16"
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
health_check_path   = "/health"

# Image
ecr_image_tag = "latest"
