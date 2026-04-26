# JWT keys (RS256)

In dev, generate a keypair:

```bash
cd smartbarrel/infra/jwt
openssl genrsa -out private.pem 4096
openssl rsa -in private.pem -pubout -out public.pem
chmod 600 private.pem
```

In prod, store the private key in Vault / K8s secrets, never in Git.
