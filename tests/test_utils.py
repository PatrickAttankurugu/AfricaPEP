from africapep.api.schemas import country_flag

def test_country_flag():
    assert country_flag("GH") == "🇬🇭"
    assert country_flag("NG") == "🇳🇬"
    assert country_flag("KE") == "🇰🇪"
    assert country_flag("ZA") == "🇿🇦"
    assert country_flag("") == ""
    assert country_flag("GHA") == ""
    assert country_flag("G") == ""
    # Test lowercase
    assert country_flag("gh") == "🇬🇭"
