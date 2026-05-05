output "api_url"          { value = module.api_gateway.api_url }
output "predict_endpoint" { value = module.api_gateway.predict_endpoint }
output "accuracy_endpoint"{ value = module.api_gateway.accuracy_endpoint }
output "simulate_endpoint"{ value = module.api_gateway.simulate_endpoint }
# output "amplify_url"      { value = module.amplify.app_url }
output "model_bucket"     { value = module.s3.bucket_name }

# output "upload_commands" {
#   value = <<-EOT
#   aws s3 cp fifa_model.pkl      s3://${module.s3.bucket_name}/fifa_model.pkl
#   aws s3 cp fifa_le_home.pkl    s3://${module.s3.bucket_name}/fifa_le_home.pkl
#   aws s3 cp fifa_le_away.pkl    s3://${module.s3.bucket_name}/fifa_le_away.pkl
#   aws s3 cp ipl_model.pkl       s3://${module.s3.bucket_name}/ipl_model.pkl
#   aws s3 cp ipl_le_t1.pkl       s3://${module.s3.bucket_name}/ipl_le_t1.pkl
#   aws s3 cp ipl_le_t2.pkl       s3://${module.s3.bucket_name}/ipl_le_t2.pkl
#   aws s3 cp ipl_le_venue.pkl    s3://${module.s3.bucket_name}/ipl_le_venue.pkl
# EOT
# }