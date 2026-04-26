from shared.auth.rbac import CurrentUser


def test_wildcard_admin():
    u = CurrentUser(id="1", email="a@b", roles=["admin"], permissions=["*:*"])
    assert u.has_permission("anything:read")


def test_resource_wildcard():
    u = CurrentUser(id="1", email="a@b", roles=["engineer"],
                    permissions=["production:*"])
    assert u.has_permission("production:read")
    assert u.has_permission("production:write")
    assert not u.has_permission("ml:train")


def test_explicit_match():
    u = CurrentUser(id="1", email="a@b", roles=["analyst"],
                    permissions=["production:read", "ml:predict"])
    assert u.has_permission("production:read")
    assert u.has_permission("ml:predict")
    assert not u.has_permission("production:write")
