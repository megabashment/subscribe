from subscribe.utils.device import detect_device


def test_detect_device_returns_valid_value():
    device = detect_device()
    assert device in ("cuda", "mps", "cpu")


def test_detect_device_override():
    assert detect_device("cpu") == "cpu"


def test_detect_device_auto_without_torch(monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, "torch", None)
    device = detect_device()
    assert device in ("cuda", "mps", "cpu")
