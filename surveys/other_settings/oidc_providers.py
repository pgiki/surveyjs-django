import os
OIDC_AUTH = {
    # Specify OpenID Connect endpoint. Configuration will be
    # automatically done based on the discovery document found
    # at <endpoint>/.well-known/openid-configuration
    'OIDC_ENDPOINT': os.getenv('OIDC_ENDPOINT'),
    # The Claims Options can now be defined by a static string.
    # ref: https://docs.authlib.org/en/latest/jose/jwt.html#jwt-payload-claims-validation
    # The old OIDC_AUDIENCES option is removed in favor of this new option.
    # `aud` is only required, when you set it as an essential claim.
    'OIDC_CLAIMS_OPTIONS': {
        'aud': {
            'values': [os.getenv('OIDC_PROVIDER_ID') or "sso"],
            'essential': False,
        }
    },
    
    # (Optional) Function that resolves id_token into user.
    # This function receives a request and an id_token dict and expects to
    # return a User object. The default implementation tries to find the user
    # based on username (natural key) taken from the 'sub'-claim of the
    # id_token.
    'OIDC_RESOLVE_USER_FUNCTION': 'oidc_auth.authentication.get_user_by_id',
    
    # (Optional) Number of seconds in the past valid tokens can be 
    # issued (default 600)
    'OIDC_LEEWAY': 600,
    
    # (Optional) Time before signing keys will be refreshed (default 24 hrs)
    'OIDC_JWKS_EXPIRATION_TIME': 24*60*60,

    # (Optional) Time before bearer token validity is verified again (default 10 minutes)
    'OIDC_BEARER_TOKEN_EXPIRATION_TIME': 10*60,
    
    # (Optional) Token prefix in JWT authorization header (default 'JWT')
    'JWT_AUTH_HEADER_PREFIX': 'JWT',
    
    # (Optional) Token prefix in Bearer authorization header (default 'Bearer')
    'BEARER_AUTH_HEADER_PREFIX': 'Bearer',

    # (Optional) Which Django cache to use
    'OIDC_CACHE_NAME': 'default',

    # (Optional) A cache key prefix when storing and retrieving cached values
    'OIDC_CACHE_PREFIX': 'oidc_auth.',
}

SOCIALACCOUNT_PROVIDERS = {
    "openid_connect": {
        'EMAIL_AUTHENTICATION': True,
        "APPS": [
            {
                "provider_id": os.getenv('OIDC_PROVIDER_ID') or "sso",
                "name": "Single Sign On (SSO)",
                "client_id": os.getenv('OIDC_CLIENT_ID'),
                "secret": os.getenv('OIDC_SECRET_KEY'),
                "settings": {
                    "server_url": f"{OIDC_AUTH['OIDC_ENDPOINT']}/.well-known/openid-configuration",
                },
            }
        ]
    }
}

SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_STORE_TOKENS = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
# 
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True

LOGIN_URL ='/accounts/login/'
LOGIN_REDIRECT_URL='/'