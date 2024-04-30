
def credentials_mapping(credentials):
    match credentials.provider:
        
        case "GCP":
            return {
                "type": credentials.type,
                "project_id": credentials.project_id,
                "private_key_id": credentials.private_key_id,
                "private_key": credentials.private_key,
                "client_email": credentials.client_email,
                "client_id": credentials.client_id,
                "auth_uri": credentials.auth_uri,
                "token_uri": credentials.token_uri,
                "auth_provider_x509_cert_url": credentials.auth_provider_url,
                "client_x509_cert_url": credentials.client_url,
                "universe_domain": credentials.universe_domain
            }
        case "AWS":
            return {
                "region": credentials.project_id,
                "access_key": credentials.private_key_id,
                "secret_access_key": credentials.private_key,
            }
