from infractl import identity


def test_sanitize():
    assert identity.sanitize('paul') == 'paul'
    assert (
            identity.sanitize('first.last1-last2@domain.com') == 'first-last1-last2-domain-com'
    )
    assert identity.sanitize('lee.foo-bar@domain.com') == 'lee-foo-bar-domain-com'
    assert identity.sanitize('.lee..foo--bar@domain.com.') == 'lee-foo-bar-domain-com'
