from services.auth_service.app.core.security import (
    generate_mfa_secret, hash_password, mfa_provisioning_uri,
    verify_mfa_code, verify_password,
)


def test_password_round_trip():
    h = hash_password("VerySecure-Password-123!", rounds=10)
    assert verify_password("VerySecure-Password-123!", h)
    assert not verify_password("wrong", h)


def test_mfa_round_trip():
    secret = generate_mfa_secret()
    import pyotp
    code = pyotp.TOTP(secret).now()
    assert verify_mfa_code(secret, code)
    assert not verify_mfa_code(secret, "000000")


def test_mfa_provisioning_uri():
    secret = generate_mfa_secret()
    uri = mfa_provisioning_uri(secret, "test@smartbarrel.td")
    assert uri.startswith("otpauth://totp/")
    assert "smartbarrel" in uri.lower()
